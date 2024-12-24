from flask import Flask, request, jsonify
from dotenv import load_dotenv
import base64
import os
import io
from PIL import Image
import pdf2image
import google.generativeai as genai
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)

# Enable CORS - Allow requests from localhost:5173 (React development server)
CORS(app, origins=["http://localhost:5173"])  # Specify the React app's origin

# Load environment variables
load_dotenv()

# Configure Google Generative AI API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Helper function to convert PDF to image and prepare for processing
def input_pdf_setup(uploaded_file):
    try:
        if uploaded_file:
            # Convert the PDF to images (first page only)
            images = pdf2image.convert_from_bytes(uploaded_file.read())
            first_page = images[0]

            # Convert image to base64
            img_byte_arr = io.BytesIO()
            first_page.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()

            pdf_parts = [
                {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(img_byte_arr).decode()  # Encode to base64
                }
            ]
            return pdf_parts
        else:
            raise ValueError("No file uploaded")
    except Exception as e:
        raise ValueError(f"Error processing PDF: {str(e)}")

# Helper function to get AI response
def get_gemini_response(job_description, pdf_content, prompt):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([job_description, pdf_content[0], prompt])
        return response.text
    except Exception as e:
        raise ValueError(f"Error generating AI response: {str(e)}")

# Health check endpoint to verify if the backend is working
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "Server is running"}), 200

# Define API endpoint for resume analysis
@app.route('/analyze-resume', methods=['POST'])
def analyze_resume():
    try:
        # Retrieve form data
        job_description = request.form.get('job_description')  # Match the key with frontend
        uploaded_file = request.files.get('resume')

        # Validate inputs
        if not job_description or not uploaded_file:
            return jsonify({"error": "Both job description and resume are required"}), 400

        # Process PDF
        pdf_content = input_pdf_setup(uploaded_file)

        # Define AI prompt
        input_prompt = """
        You are an experienced Technical Human Resource Manager. 
        Your task is to review the provided resume against the job description. 
        Highlight the strengths and weaknesses of the applicant in relation to the specified job requirements.
        """

        # Get AI response
        ai_response = get_gemini_response(job_description, pdf_content, input_prompt)

        # Return response as JSON
        return jsonify({"response": ai_response}), 200

    except Exception as e:
        return jsonify({"error": f"Error analyzing resume: {str(e)}"}), 500

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
