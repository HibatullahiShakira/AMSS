import os
import json
import pandas as pd
from datetime import datetime
from io import BytesIO

from django.http import HttpResponse, JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from users.models import User
from rest_framework_simplejwt.models import TokenUser
from finance.models import Customer, Supplier, Expense, Employee
from billing.models import Invoice, Product
from finance.models_accounting import Transaction

from .permissions import IsOwnerOrAdmin

class DataManagementViewSet(viewsets.ViewSet):
    permission_classes = [IsOwnerOrAdmin]

    def _get_business(self, request):
        user = request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)
        return getattr(user, 'business', None)

    @action(detail=False, methods=['get'], url_path='export')
    def export_data(self, request):
        business = self._get_business(request)
        if not business:
            return Response({"error": "No business context found."}, status=status.HTTP_400_BAD_REQUEST)

        # Gather data
        customers = Customer.objects.filter(business=business).values('name', 'email', 'phone', 'contact_info', 'created_at')
        suppliers = Supplier.objects.filter(business=business).values('name', 'email', 'phone', 'contact_info', 'created_at')
        expenses = Expense.objects.filter(business=business).values('description', 'amount', 'date', 'category', 'status')
        invoices = Invoice.objects.filter(business=business).values('invoice_number', 'customer__name', 'issue_date', 'due_date', 'total_amount', 'status')
        transactions = Transaction.objects.filter(business=business).values('date', 'description', 'amount', 'transaction_type', 'is_reconciled')
        products = Product.objects.filter(business=business).values('name', 'sku', 'unit_price', 'quantity_on_hand', 'category')
        employees = Employee.objects.filter(business=business).values('first_name', 'last_name', 'email', 'role', 'salary', 'is_active')

        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame(list(customers)).to_excel(writer, sheet_name='Customers', index=False)
            pd.DataFrame(list(suppliers)).to_excel(writer, sheet_name='Suppliers', index=False)
            pd.DataFrame(list(expenses)).to_excel(writer, sheet_name='Expenses', index=False)
            pd.DataFrame(list(invoices)).to_excel(writer, sheet_name='Invoices', index=False)
            pd.DataFrame(list(transactions)).to_excel(writer, sheet_name='Transactions', index=False)
            pd.DataFrame(list(products)).to_excel(writer, sheet_name='Products', index=False)
            pd.DataFrame(list(employees)).to_excel(writer, sheet_name='Employees', index=False)

        output.seek(0)
        
        filename = f"AMSS_Export_{business.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(detail=False, methods=['post'], url_path='import')
    def import_data(self, request):
        business = self._get_business(request)
        if not business:
            return Response({"error": "No business context found."}, status=400)

        file = request.FILES.get('file')

        if not file:
            return Response({"error": "File is required."}, status=400)

        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith('.xlsx') or file.name.endswith('.xls'):
                df = pd.read_excel(file)
            else:
                return Response({"error": "Unsupported file format. Please upload CSV or Excel."}, status=400)

            records_created = 0
            
            # Auto-detect target table based on columns
            cols = [str(c).lower().strip() for c in df.columns]
            
            target_table = 'unknown'
            if 'username' in cols and 'role' in cols:
                target_table = 'employees'
            elif 'contact id' in cols or 'customer group' in cols or ('business name' in cols and 'total sale due' in cols):
                target_table = 'customers'
            elif 'description' in cols and 'amount' in cols:
                target_table = 'expenses'
            elif 'price' in cols or 'unit_price' in cols or 'quantity' in cols:
                target_table = 'products'
            elif request.data.get('target_table'):
                target_table = request.data.get('target_table') # Fallback if provided

            # Simple mapping logic based on target_table
            if target_table == 'customers':
                for _, row in df.iterrows():
                    # Handle their specific CSV format for Customers
                    name = str(row.get('Business Name', row.get('Name', row.get('name', '')))).strip()
                    if not name or str(name).lower() == 'nan':
                        # Fallback to Name column if Business Name is empty
                        name = str(row.get('Name', '')).strip()
                        if not name or str(name).lower() == 'nan':
                            continue
                    
                    contact = str(row.get('Mobile', row.get('Email', row.get('email', '')))).strip()
                    if contact.lower() == 'nan': contact = ''
                    
                    # Prevent duplicates by name (case insensitive)
                    if not Customer.objects.filter(business=business, name__iexact=name).exists():
                        Customer.objects.create(
                            business=business,
                            user=request.user if not isinstance(request.user, TokenUser) else User.objects.get(id=request.user.id),
                            name=name[:255],
                            contact_info=contact[:255]
                        )
                        records_created += 1

            elif target_table == 'expenses':
                for _, row in df.iterrows():
                    desc = str(row.get('description', '')).strip()
                    amount = pd.to_numeric(row.get('amount', 0), errors='coerce')
                    date_val = row.get('date', datetime.now().date())
                    
                    if pd.isna(amount) or not desc:
                        continue
                        
                    Expense.objects.create(
                        business=business,
                        user=request.user if not isinstance(request.user, TokenUser) else User.objects.get(id=request.user.id),
                        description=desc,
                        amount=amount,
                        date=date_val if isinstance(date_val, str) else datetime.now().date()
                    )
                    records_created += 1

            elif target_table == 'products':
                for _, row in df.iterrows():
                    name = str(row.get('name', '')).strip()
                    if not name or str(name).lower() == 'nan':
                        continue
                        
                    price = pd.to_numeric(row.get('unit_price', row.get('price', 0)), errors='coerce')
                    qty = pd.to_numeric(row.get('quantity', row.get('quantity_on_hand', 0)), errors='coerce')
                    
                    if not Product.objects.filter(business=business, name__iexact=name).exists():
                        Product.objects.create(
                            business=business,
                            name=name,
                            sku=str(row.get('sku', '')).strip()[:50],
                            unit_price=price if not pd.isna(price) else 0,
                            quantity_on_hand=qty if not pd.isna(qty) else 0
                        )
                        records_created += 1

            elif target_table == 'employees':
                for _, row in df.iterrows():
                    # Handle their specific CSV format for Employees
                    name = str(row.get('Name', row.get('first_name', ''))).strip()
                    if not name or str(name).lower() == 'nan':
                        continue
                        
                    salary = pd.to_numeric(row.get('salary', 0), errors='coerce')
                    email = str(row.get('Email', row.get('email', ''))).strip()
                    if email.lower() == 'nan': email = ''
                    role = str(row.get('Role', row.get('role', 'Staff'))).strip()
                    if role.lower() == 'nan': role = 'Staff'
                    
                    if not Employee.objects.filter(business=business, name__iexact=name).exists():
                        Employee.objects.create(
                            business=business,
                            name=name,
                            role=role,
                            salary=salary if not pd.isna(salary) else 0,
                            start_date=datetime.now().date()
                        )
                        records_created += 1

            else:
                return Response({"error": "Could not auto-detect the table from the file columns. Please check your file format."}, status=400)

            return Response({
                "message": f"Successfully imported {records_created} records into {target_table}.",
                "records_created": records_created
            })

        except Exception as e:
            return Response({"error": f"Failed to process file: {str(e)}"}, status=500)


class DocumentParseViewSet(viewsets.ViewSet):
    permission_classes = [IsOwnerOrAdmin]

    @action(detail=False, methods=['post'], url_path='parse')
    def parse_document(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        text_content = ""
        try:
            # 1. Extract Text
            if file.name.lower().endswith('.pdf'):
                try:
                    import pdfplumber
                    with pdfplumber.open(file) as pdf:
                        for page in pdf.pages:
                            extracted = page.extract_text()
                            if extracted:
                                text_content += extracted + "\n"
                except ImportError:
                    return Response({"error": "pdfplumber is not installed on the server."}, status=500)
            else:
                # If it's a CSV or text file representing a bill
                text_content = file.read().decode('utf-8', errors='ignore')

            if not text_content.strip():
                return Response({"error": "Could not extract text from document."}, status=400)

            # 2. Use AI to parse the text into structured JSON
            from langchain_ollama import ChatOllama
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import JsonOutputParser

            llm = ChatOllama(model="llama3:latest", format="json", temperature=0)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert AI accounting assistant. 
                Extract the following information from the invoice/receipt text and return it ONLY as a valid JSON object.
                Required keys:
                - "vendor": (string) The name of the company or person charging the money.
                - "date": (string) The date of the invoice in YYYY-MM-DD format.
                - "amount": (float) The total final amount charged. 
                - "description": (string) A short summary of what was purchased (max 5 words).
                - "expense_type": (string) Either "OPEX" for operating expenses (like rent, utilities, software, services) or "STOCK" for physical products/inventory bought to be resold.
                
                If a field cannot be found, leave it as null."""),
                ("user", "Here is the document text:\n{text}")
            ])

            parser = JsonOutputParser()
            chain = prompt | llm | parser

            # In a production setting, you'd run this asynchronously or handle timeouts
            result = chain.invoke({"text": text_content[:5000]}) # Limit text length for safety

            return Response({
                "message": "Document parsed successfully.",
                "extracted_data": result
            })

        except Exception as e:
            import traceback
            return Response({
                "error": f"Failed to parse document: {str(e)}",
                "traceback": traceback.format_exc()
            }, status=500)
