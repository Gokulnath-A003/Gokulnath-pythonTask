from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from .forms import UploadFileForm
import pandas as pd
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            fs = FileSystemStorage()
            file_path = fs.save(uploaded_file.name, uploaded_file)

            # Load the file into a DataFrame
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(fs.path(file_path))
            else:
                df = pd.read_excel(fs.path(file_path), sheet_name=0)

            # Clean the DataFrame
            df.dropna(how='all', inplace=True)  # Drop any rows where all elements are NaN
            df.columns = df.columns.str.strip()  # Clean column names

            # Debugging: Print the first few rows of the DataFrame
            print("Loaded DataFrame:")
            print(df.head())

            # Convert Cust Pin to string to match the text format in the CSV
            df['Cust Pin'] = df['Cust Pin'].astype(str)

            # Define the criteria for filtering
            desired_states = ["ARUNACHAL PRADESH", "JHARKHAND"]
            desired_pins = [str(pin) for pin in [791121, 791112, 816101, 816108]]  # Convert to string

            # Apply filters
            filtered_df = df[
                (df['Cust State'].isin(desired_states)) &
                (df['Cust Pin'].isin(desired_pins)) 
            ]

            # Debugging: Print filtered DataFrame
            print("Filtered DataFrame:")
            print(filtered_df)

            # Group by Cust State and Cust Pin, then count occurrences
            result_df = filtered_df.groupby(['Cust State', 'Cust Pin']).size().reset_index(name='DPD')

            # Get total records
            total_records = len(result_df)

            # Prepare HTML content for the email
            html_content = """
            <html>
                <body>
                    <h3>Summary Report</h3>
                    <p>Total Records: {total_records}</p>
                    <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 80%;">
                        <thead>
                            <tr style="background-color: #f2f2f2;">
                                <th>Cust State</th>
                                <th>Cust Pin</th>
                                <th>DPD (Count)</th>
                            </tr>
                        </thead>
                        <tbody>
            """.format(total_records=total_records)

            # Check if there are records to include in the email
            if total_records > 0:
                # Populate the table with grouped data
                for _, row in result_df.iterrows():
                    html_content += f"""
                        <tr>
                            <td>{row['Cust State']}</td>
                            <td>{row['Cust Pin']}</td>
                            <td>{row['DPD']}</td>
                        </tr>
                    """
            else:
                html_content += """
                    <tr>
                        <td colspan="3" style="text-align: center;">No records found for the specified criteria.</td>
                    </tr>
                """

            # Close the table in the HTML
            html_content += """
                        </tbody>
                    </table>
                </body>
            </html>
            """

            # Prepare and send the email
            email_subject = 'Python Assignment - Gokulnath A'
            email = EmailMultiAlternatives(
                subject=email_subject,
                body=strip_tags(html_content),
                from_email='kitcbe.25.21bcb018@gmail.com',  # Replace with your sender email
                to=['kitcbe.25.21bcb018@gmail.com']        # Replace with the recipient's email
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

            # Render the success page
            return render(request, 'file_upload/success.html', {'total_records': total_records})
    else:
        form = UploadFileForm()
    return render(request, 'file_upload/upload.html', {'form': form})
