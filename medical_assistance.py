import re
import PyPDF2
import streamlit as st
from twilio.rest import Client
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
from datetime import datetime

# Twilio Configuration
TWILIO_SID = "enter your id"
TWILIO_AUTH = "enter your identifier"
TWILIO_PHONE = "enter your phone number "

client = Client(TWILIO_SID, TWILIO_AUTH)

# Comprehensive Reference Ranges
REFERENCE_RANGES = {
    # Hematology
    "Hemoglobin": {"male": (13.8, 17.2), "female": (12.1, 15.1), "unit": "g/dL"},
    "Hematocrit": {"male": (40.7, 50.3), "female": (36.1, 44.3), "unit": "%"},
    "RBC Count": {"male": (4.7, 6.1), "female": (4.2, 5.4), "unit": "million/μL"},
    "WBC Count": {"all": (4.5, 11.0), "unit": "thousand/μL"},
    "Platelet Count": {"all": (150, 450), "unit": "thousand/μL"},
    "MCV": {"all": (80, 100), "unit": "fL"},
    "MCH": {"all": (27, 32), "unit": "pg"},
    "MCHC": {"all": (32, 36), "unit": "g/dL"},
    "ESR": {"male": (0, 22), "female": (0, 29), "unit": "mm/hr"},

    # Lipid Profile
    "Total Cholesterol": {"all": (0, 200), "unit": "mg/dL"},
    "LDL Cholesterol": {"all": (0, 100), "unit": "mg/dL"},
    "HDL Cholesterol": {"male": (40, 100), "female": (50, 100), "unit": "mg/dL"},
    "Triglycerides": {"all": (0, 150), "unit": "mg/dL"},
    "VLDL": {"all": (5, 40), "unit": "mg/dL"},

    # Diabetes Markers
    "Fasting Blood Sugar": {"all": (70, 100), "unit": "mg/dL"},
    "Random Blood Sugar": {"all": (70, 140), "unit": "mg/dL"},
    "HbA1c": {"all": (4.0, 5.6), "unit": "%"},
    "Post Meal Sugar": {"all": (70, 140), "unit": "mg/dL"},

    # Liver Function
    "SGPT": {"all": (7, 56), "unit": "U/L"},
    "SGOT": {"all": (10, 40), "unit": "U/L"},
    "Alkaline Phosphatase": {"all": (44, 147), "unit": "U/L"},
    "Total Bilirubin": {"all": (0.3, 1.2), "unit": "mg/dL"},
    "Direct Bilirubin": {"all": (0.0, 0.3), "unit": "mg/dL"},
    "Total Protein": {"all": (6.0, 8.3), "unit": "g/dL"},
    "Albumin": {"all": (3.5, 5.0), "unit": "g/dL"},

    # Kidney Function
    "Creatinine": {"male": (0.74, 1.35), "female": (0.59, 1.04), "unit": "mg/dL"},
    "Blood Urea": {"all": (6, 20), "unit": "mg/dL"},
    "Uric Acid": {"male": (3.4, 7.0), "female": (2.4, 6.0), "unit": "mg/dL"},
    "eGFR": {"all": (90, 120), "unit": "mL/min/1.73m²"},

    # Thyroid Function
    "TSH": {"all": (0.27, 4.2), "unit": "μIU/mL"},
    "T3": {"all": (80, 200), "unit": "ng/dL"},
    "T4": {"all": (5.1, 14.1), "unit": "μg/dL"},
    "Free T3": {"all": (2.0, 4.4), "unit": "pg/mL"},
    "Free T4": {"all": (0.93, 1.7), "unit": "ng/dL"},

    # Electrolytes
    "Sodium": {"all": (136, 145), "unit": "mEq/L"},
    "Potassium": {"all": (3.5, 5.1), "unit": "mEq/L"},
    "Chloride": {"all": (96, 106), "unit": "mEq/L"},
    "Calcium": {"all": (8.7, 10.2), "unit": "mg/dL"},
    "Phosphorus": {"all": (2.5, 4.5), "unit": "mg/dL"},
    "Magnesium": {"all": (1.7, 2.2), "unit": "mg/dL"},

    # Vitamins
    "Vitamin D": {"all": (30, 100), "unit": "ng/mL"},
    "Vitamin B12": {"all": (211, 946), "unit": "pg/mL"},
    "Folate": {"all": (2.7, 17.0), "unit": "ng/mL"},
    "Iron": {"male": (65, 176), "female": (50, 170), "unit": "μg/dL"},
    "Ferritin": {"male": (12, 300), "female": (12, 150), "unit": "ng/mL"},

    # Urine Analysis
    "Urine Protein": {"all": (0, 0), "unit": "mg/dL"},
    "Urine Sugar": {"all": (0, 0), "unit": "mg/dL"},
    "Urine Ketones": {"all": (0, 0), "unit": "mg/dL"},
    "Specific Gravity": {"all": (1.005, 1.030), "unit": ""},
    "pH": {"all": (4.6, 8.0), "unit": ""},

    # Cardiac Markers
    "CK-MB": {"all": (0, 6.3), "unit": "ng/mL"},
    "Troponin I": {"all": (0, 0.04), "unit": "ng/mL"},
    "LDH": {"all": (140, 280), "unit": "U/L"},

    # Inflammatory Markers
    "CRP": {"all": (0, 3.0), "unit": "mg/L"},
    "Procalcitonin": {"all": (0, 0.25), "unit": "ng/mL"}
}

# Comprehensive Medical Explanations
EXPLANATIONS = {
    "Hemoglobin": {
        "low": "Low hemoglobin indicates anemia, which can cause fatigue, weakness, pale skin, shortness of breath, and cold hands and feet. Common causes include iron deficiency, chronic diseases, blood loss, or nutritional deficiencies.",
        "high": "High hemoglobin may indicate dehydration, living at high altitude, lung disease, or certain blood disorders. It can increase blood thickness and risk of clots.",
        "normal": "Normal hemoglobin levels indicate good oxygen-carrying capacity and healthy red blood cell production."
    },
    "Total Cholesterol": {
        "low": "Very low cholesterol may indicate malnutrition, liver disease, hyperthyroidism, or certain genetic conditions.",
        "high": "High cholesterol increases risk of heart disease, stroke, and atherosclerosis. It may be due to diet, genetics, obesity, diabetes, or sedentary lifestyle.",
        "normal": "Normal cholesterol levels support cardiovascular health and proper cell membrane function."
    },
    "Fasting Blood Sugar": {
        "low": "Low blood sugar (hypoglycemia) can cause dizziness, sweating, confusion, irritability, and in severe cases, unconsciousness.",
        "high": "High fasting blood sugar may indicate prediabetes or diabetes, increasing risk of complications affecting eyes, kidneys, nerves, and blood vessels.",
        "normal": "Normal fasting blood sugar indicates good glucose metabolism and insulin function."
    },
    "TSH": {
        "low": "Low TSH suggests hyperthyroidism, which can cause weight loss, rapid heartbeat, anxiety, tremors, and heat intolerance.",
        "high": "High TSH indicates hypothyroidism, which can cause weight gain, fatigue, depression, cold intolerance, and dry skin.",
        "normal": "Normal TSH levels indicate balanced thyroid function and proper metabolism regulation."
    },
    "Creatinine": {
        "low": "Low creatinine may indicate decreased muscle mass, severe liver disease, or pregnancy.",
        "high": "High creatinine suggests kidney dysfunction, which may lead to fluid retention, electrolyte imbalances, and toxin buildup.",
        "normal": "Normal creatinine levels indicate healthy kidney function and proper waste filtration."
    },
    "SGPT": {
        "low": "Low SGPT is generally not concerning and may indicate good liver health.",
        "high": "High SGPT suggests liver cell damage, which may be due to hepatitis, fatty liver, alcohol consumption, or certain medications.",
        "normal": "Normal SGPT levels indicate healthy liver function and proper enzyme activity."
    },
    "HDL Cholesterol": {
        "low": "Low HDL (good cholesterol) increases risk of heart disease as it helps remove bad cholesterol from arteries.",
        "high": "High HDL cholesterol is protective against heart disease and stroke.",
        "normal": "Normal HDL levels help protect against cardiovascular disease."
    },
    "LDL Cholesterol": {
        "low": "Very low LDL may be beneficial for heart health but could indicate underlying conditions if extremely low.",
        "high": "High LDL (bad cholesterol) increases risk of atherosclerosis, heart attack, and stroke.",
        "normal": "Normal LDL levels support cardiovascular health."
    },
    "HbA1c": {
        "low": "Low HbA1c generally indicates good glucose control but may suggest frequent low blood sugar episodes.",
        "high": "High HbA1c indicates poor glucose control over the past 2-3 months, increasing diabetic complications risk.",
        "normal": "Normal HbA1c indicates excellent long-term glucose control."
    },
    "Vitamin D": {
        "low": "Low vitamin D can cause bone weakness, muscle pain, increased infection risk, and mood disorders.",
        "high": "Very high vitamin D may cause nausea, vomiting, kidney stones, and calcium buildup in soft tissues.",
        "normal": "Normal vitamin D levels support bone health, immune function, and overall well-being."
    }
}

# Comprehensive Diet and Lifestyle Plans
DIET_PLANS = {
    "Hemoglobin": {
        "low": {
            "diet": "Iron-rich foods: Red meat (lean beef, lamb), poultry (chicken, turkey), fish (tuna, salmon), shellfish. Plant sources: Spinach, kale, swiss chard, lentils, chickpeas, kidney beans, quinoa, fortified cereals, pumpkin seeds, dark chocolate. Enhance iron absorption with vitamin C: citrus fruits, bell peppers, strawberries, tomatoes, broccoli. Avoid tea, coffee, dairy, and calcium supplements with iron-rich meals.",
            "lifestyle": "Cook in cast iron pans, avoid excessive tea/coffee consumption, manage heavy menstrual periods, check for underlying bleeding, take iron supplements as prescribed by doctor.",
            "warning": "Persistent anemia requires medical evaluation to rule out underlying causes like internal bleeding, chronic diseases, or nutritional deficiencies."
        },
        "high": {
            "diet": "Stay well-hydrated with 8-10 glasses of water daily. Limit iron-rich foods and iron supplements unless medically necessary. Include foods that may help thin blood naturally: garlic, ginger, turmeric, fatty fish.",
            "lifestyle": "Avoid smoking, maintain healthy weight, exercise regularly but avoid overexertion at high altitudes, monitor oxygen levels if living at high altitude.",
            "warning": "High hemoglobin may indicate underlying lung or heart conditions requiring medical evaluation."
        }
    },
    "Total Cholesterol": {
        "high": {
            "diet": "Soluble fiber foods: Oats, barley, beans, lentils, apples, citrus fruits. Healthy fats: Olive oil, avocados, nuts (almonds, walnuts), seeds, fatty fish (salmon, mackerel, sardines). Plant sterols: Fortified margarine, nuts, seeds. Avoid: Trans fats, saturated fats, fried foods, processed meats, full-fat dairy, baked goods with hydrogenated oils.",
            "lifestyle": "Exercise 30 minutes daily (brisk walking, swimming, cycling), maintain healthy weight, quit smoking, limit alcohol consumption, manage stress through meditation or yoga.",
            "warning": "High cholesterol requires lifestyle modification and possibly medication to prevent cardiovascular disease."
        },
        "low": {
            "diet": "Include healthy fats: Olive oil, nuts, seeds, avocados, fatty fish. Ensure adequate calories and protein. Consider omega-3 supplements if recommended by doctor.",
            "lifestyle": "Regular health monitoring, ensure adequate nutrition, address any underlying conditions affecting cholesterol synthesis.",
            "warning": "Very low cholesterol may indicate underlying liver disease, malnutrition, or other medical conditions."
        }
    },
    "Fasting Blood Sugar": {
        "high": {
            "diet": "Low glycemic index foods: Non-starchy vegetables (broccoli, spinach, cauliflower), whole grains (brown rice, quinoa, oats), legumes, lean proteins (fish, chicken breast, tofu). Portion control: Use smaller plates, measure carbohydrates. Avoid: Sugary drinks, white bread, white rice, pastries, processed foods, high-sugar fruits in excess.",
            "lifestyle": "Regular exercise (150 minutes moderate activity weekly), weight management, stress reduction, adequate sleep (7-9 hours), blood sugar monitoring as recommended, medication compliance if prescribed.",
            "warning": "High blood sugar requires immediate medical attention to prevent diabetic complications affecting eyes, kidneys, nerves, and blood vessels."
        },
        "low": {
            "diet": "Regular, balanced meals every 3-4 hours. Complex carbohydrates: Whole grain bread, oats, sweet potatoes. Include protein with each meal. Keep quick-acting carbohydrates available: glucose tablets, fruit juice, honey.",
            "lifestyle": "Monitor blood sugar regularly, avoid skipping meals, adjust exercise timing and intensity, carry emergency glucose, educate family about hypoglycemia management.",
            "warning": "Frequent hypoglycemia requires medical evaluation to adjust medications and identify underlying causes."
        }
    },
    "TSH": {
        "high": {
            "diet": "Iodine-rich foods: Iodized salt, seafood, dairy products, eggs. Selenium sources: Brazil nuts, tuna, sardines, turkey. Avoid excessive raw cruciferous vegetables (cabbage, broccoli, cauliflower) which may interfere with thyroid function.",
            "lifestyle": "Take thyroid medication on empty stomach as prescribed, regular follow-up testing, maintain consistent medication timing, avoid soy supplements that may interfere with medication absorption.",
            "warning": "Hypothyroidism requires lifelong thyroid hormone replacement therapy and regular monitoring."
        },
        "low": {
            "diet": "Limit iodine intake, avoid kelp and iodine supplements. Include calcium-rich foods: Low-fat dairy, leafy greens, sardines. Antioxidant-rich foods: Berries, green tea, colorful vegetables.",
            "lifestyle": "Take prescribed antithyroid medications, avoid excessive physical stress, maintain cool environment, monitor heart rate and blood pressure, regular medical follow-up.",
            "warning": "Hyperthyroidism can cause serious cardiac complications and requires prompt medical treatment."
        }
    },
    "Creatinine": {
        "high": {
            "diet": "Low-protein diet (0.6-0.8g/kg body weight) - consult dietitian. Limit: Red meat, poultry, fish, dairy. Restrict sodium (less than 2300mg daily), potassium, and phosphorus based on kidney function. Stay hydrated but follow fluid restrictions if advised.",
            "lifestyle": "Monitor blood pressure closely, avoid nephrotoxic medications (NSAIDs, certain antibiotics), regular kidney function monitoring, manage diabetes and hypertension strictly.",
            "warning": "Elevated creatinine indicates kidney dysfunction requiring immediate medical evaluation and possible specialist referral."
        }
    },
    "SGPT": {
        "high": {
            "diet": "Liver-friendly foods: Leafy greens, cruciferous vegetables, berries, garlic, turmeric, green tea. Avoid: Alcohol completely, processed foods, excessive fats, high-sugar foods, acetaminophen overuse.",
            "lifestyle": "Complete alcohol cessation, weight loss if overweight, regular exercise, avoid unnecessary medications and supplements, hepatitis vaccination if indicated.",
            "warning": "Elevated liver enzymes require medical evaluation to identify and treat underlying liver conditions."
        }
    }
}


# Utility Functions
def extract_text_from_pdf(file):
    """Extract text content from uploaded PDF file"""
    text = ""
    try:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
    return text


def parse_values(text):
    """Extract medical test values from text using pattern matching"""
    results = {}

    # Enhanced pattern matching for various test formats
    patterns = [
        r"(?i)({test})\s*[:\-]?\s*(\d+\.?\d*)",
        r"(?i)({test})\s*[:\-]?\s*(\d+\.?\d*)\s*(?:mg/dl|g/dl|u/l|ng/ml|pg/ml|miu/ml|meq/l)",
        r"(?i)({test})\s*[:\-]?\s*(\d+\.?\d*)\s*%",
    ]

    for test in REFERENCE_RANGES.keys():
        for pattern in patterns:
            formatted_pattern = pattern.format(test=re.escape(test))
            match = re.search(formatted_pattern, text)
            if match:
                try:
                    results[test] = float(match.group(2))
                    break
                except (ValueError, IndexError):
                    continue

    return results


def determine_gender_range(test, gender="all"):
    """Determine appropriate reference range based on gender"""
    ranges = REFERENCE_RANGES[test]
    if gender in ranges:
        return ranges[gender]
    elif "all" in ranges:
        return ranges["all"]
    else:
        # Default to male range if gender-specific ranges exist but gender not specified
        return ranges.get("male", ranges.get("female", (0, 0)))


def analyze_results(results, gender="all"):
    """Analyze test results against reference ranges"""
    analysis = {}

    for test, value in results.items():
        if test not in REFERENCE_RANGES:
            continue

        low, high = determine_gender_range(test, gender)
        unit = REFERENCE_RANGES[test]["unit"]

        if value < low:
            status = "low"
        elif value > high:
            status = "high"
        else:
            status = "normal"

        explanation = EXPLANATIONS.get(test, {}).get(status, f"{test} is {status}")

        analysis[test] = {
            "value": value,
            "unit": unit,
            "range": (low, high),
            "status": status,
            "explanation": explanation
        }

    return analysis


def find_hospitals(city, test_types):
    """Find recommended hospitals based on city and required medical tests"""

    # Hospital database with specializations and ratings
    hospital_database = {
        "mumbai": {
            "premium": [
                {"name": "Kokilaben Dhirubhai Ambani Hospital",
                 "specialties": ["Cardiology", "Endocrinology", "Nephrology"], "rating": 4.8,
                 "type": "Multi-specialty"},
                {"name": "Lilavati Hospital", "specialties": ["Internal Medicine", "Pathology"], "rating": 4.6,
                 "type": "Multi-specialty"},
                {"name": "Breach Candy Hospital", "specialties": ["Cardiology", "Diabetes Care"], "rating": 4.7,
                 "type": "Multi-specialty"}
            ],
            "affordable": [
                {"name": "KEM Hospital", "specialties": ["General Medicine", "Pathology"], "rating": 4.2,
                 "type": "Government"},
                {"name": "Sion Hospital", "specialties": ["Internal Medicine", "Endocrinology"], "rating": 4.0,
                 "type": "Government"},
                {"name": "King Edward Memorial Hospital", "specialties": ["General Medicine"], "rating": 4.1,
                 "type": "Government"}
            ]
        },
        "delhi": {
            "premium": [
                {"name": "Apollo Hospital Delhi", "specialties": ["Cardiology", "Endocrinology", "Nephrology"],
                 "rating": 4.9, "type": "Multi-specialty"},
                {"name": "Max Super Speciality Hospital", "specialties": ["Internal Medicine", "Diabetes Care"],
                 "rating": 4.7, "type": "Multi-specialty"},
                {"name": "Fortis Hospital", "specialties": ["Cardiology", "Pathology"], "rating": 4.6,
                 "type": "Multi-specialty"}
            ],
            "affordable": [
                {"name": "AIIMS Delhi", "specialties": ["All Specialties"], "rating": 4.8, "type": "Government"},
                {"name": "Safdarjung Hospital", "specialties": ["Internal Medicine", "Endocrinology"], "rating": 4.1,
                 "type": "Government"},
                {"name": "Ram Manohar Lohia Hospital", "specialties": ["General Medicine"], "rating": 4.0,
                 "type": "Government"}
            ]
        },
        "bangalore": {
            "premium": [
                {"name": "Manipal Hospital", "specialties": ["Cardiology", "Endocrinology", "Nephrology"],
                 "rating": 4.8, "type": "Multi-specialty"},
                {"name": "Apollo Hospital Bangalore", "specialties": ["Internal Medicine", "Diabetes Care"],
                 "rating": 4.7, "type": "Multi-specialty"},
                {"name": "Narayana Health", "specialties": ["Cardiology", "Pathology"], "rating": 4.6,
                 "type": "Multi-specialty"}
            ],
            "affordable": [
                {"name": "Victoria Hospital", "specialties": ["General Medicine", "Pathology"], "rating": 4.2,
                 "type": "Government"},
                {"name": "Bowring Hospital", "specialties": ["Internal Medicine"], "rating": 4.0, "type": "Government"},
                {"name": "KC General Hospital", "specialties": ["General Medicine", "Endocrinology"], "rating": 4.1,
                 "type": "Government"}
            ]
        },
        "chennai": {
            "premium": [
                {"name": "Apollo Hospital Chennai", "specialties": ["Cardiology", "Endocrinology", "Nephrology"],
                 "rating": 4.9, "type": "Multi-specialty"},
                {"name": "Fortis Malar Hospital", "specialties": ["Internal Medicine", "Diabetes Care"], "rating": 4.6,
                 "type": "Multi-specialty"},
                {"name": "MIOT International", "specialties": ["Cardiology", "Pathology"], "rating": 4.7,
                 "type": "Multi-specialty"}
            ],
            "affordable": [
                {"name": "Stanley Medical College Hospital", "specialties": ["General Medicine", "Pathology"],
                 "rating": 4.1, "type": "Government"},
                {"name": "Rajiv Gandhi Government Hospital", "specialties": ["Internal Medicine"], "rating": 4.0,
                 "type": "Government"},
                {"name": "Kilpauk Medical College Hospital", "specialties": ["General Medicine", "Endocrinology"],
                 "rating": 4.2, "type": "Government"}
            ]
        },
        "hyderabad": {
            "premium": [
                {"name": "Apollo Hospital Hyderabad", "specialties": ["Cardiology", "Endocrinology", "Nephrology"],
                 "rating": 4.8, "type": "Multi-specialty"},
                {"name": "Yashoda Hospitals", "specialties": ["Internal Medicine", "Diabetes Care"], "rating": 4.6,
                 "type": "Multi-specialty"},
                {"name": "Continental Hospitals", "specialties": ["Cardiology", "Pathology"], "rating": 4.7,
                 "type": "Multi-specialty"}
            ],
            "affordable": [
                {"name": "Osmania General Hospital", "specialties": ["General Medicine", "Pathology"], "rating": 4.0,
                 "type": "Government"},
                {"name": "Gandhi Hospital", "specialties": ["Internal Medicine"], "rating": 3.9, "type": "Government"},
                {"name": "Niloufer Hospital", "specialties": ["General Medicine"], "rating": 4.1, "type": "Government"}
            ]
        },
        "kolkata": {
            "premium": [
                {"name": "Apollo Gleneagles Hospital", "specialties": ["Cardiology", "Endocrinology", "Nephrology"],
                 "rating": 4.7, "type": "Multi-specialty"},
                {"name": "Fortis Hospital Kolkata", "specialties": ["Internal Medicine", "Diabetes Care"],
                 "rating": 4.6, "type": "Multi-specialty"},
                {"name": "Rabindranath Tagore Hospital", "specialties": ["Cardiology", "Pathology"], "rating": 4.5,
                 "type": "Multi-specialty"}
            ],
            "affordable": [
                {"name": "Medical College Hospital", "specialties": ["General Medicine", "Pathology"], "rating": 4.1,
                 "type": "Government"},
                {"name": "SSKM Hospital", "specialties": ["Internal Medicine", "Endocrinology"], "rating": 4.0,
                 "type": "Government"},
                {"name": "NRS Medical College", "specialties": ["General Medicine"], "rating": 3.9,
                 "type": "Government"}
            ]
        },
        "pune": {
            "premium": [
                {"name": "Ruby Hall Clinic", "specialties": ["Cardiology", "Endocrinology", "Nephrology"],
                 "rating": 4.6, "type": "Multi-specialty"},
                {"name": "Manipal Hospital Pune", "specialties": ["Internal Medicine", "Diabetes Care"], "rating": 4.5,
                 "type": "Multi-specialty"},
                {"name": "Sahyadri Hospital", "specialties": ["Cardiology", "Pathology"], "rating": 4.4,
                 "type": "Multi-specialty"}
            ],
            "affordable": [
                {"name": "Sassoon General Hospital", "specialties": ["General Medicine", "Pathology"], "rating": 4.0,
                 "type": "Government"},
                {"name": "B.J. Medical College", "specialties": ["Internal Medicine"], "rating": 3.9,
                 "type": "Government"},
                {"name": "Aundh Civil Hospital", "specialties": ["General Medicine"], "rating": 3.8,
                 "type": "Government"}
            ]
        }
    }

    city_lower = city.lower().strip()

    # Find city in database
    if city_lower not in hospital_database:
        return None

    return hospital_database[city_lower]


def display_hospital_recommendations(city, urgent_tests):
    """Display hospital recommendations based on city and urgent test types"""
    hospitals = find_hospitals(city, urgent_tests)

    if not hospitals:
        st.warning(
            f"Hospital recommendations not available for {city}. Please search for nearby hospitals or consult your local healthcare directory.")
        return

    st.header(f" Recommended Hospitals in {city.title()}")
    st.markdown("Based on your test results, here are recommended hospitals for immediate consultation:")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(" Premium Hospitals")
        st.markdown("*Best facilities and specialists*")

        for hospital in hospitals["premium"]:
            with st.expander(f"{hospital['name']} - Rating: {hospital['rating']}/5.0"):
                st.write(f"**Type:** {hospital['type']}")
                st.write(f"**Specialties:** {', '.join(hospital['specialties'])}")
                st.write(f"**Rating:** {'' * int(hospital['rating'])} ({hospital['rating']}/5.0)")
                if hospital['rating'] >= 4.5:
                    st.success("Highly Recommended")
                elif hospital['rating'] >= 4.0:
                    st.info("Recommended")

    with col2:
        st.subheader(" Affordable Hospitals")
        st.markdown("*Government hospitals with quality care*")

        for hospital in hospitals["affordable"]:
            with st.expander(f"{hospital['name']} - Rating: {hospital['rating']}/5.0"):
                st.write(f"**Type:** {hospital['type']}")
                st.write(f"**Specialties:** {', '.join(hospital['specialties'])}")
                st.write(f"**Rating:** {'' * int(hospital['rating'])} ({hospital['rating']}/5.0)")
                if hospital['rating'] >= 4.0:
                    st.success("Good Option")
                else:
                    st.info("Basic Care Available")

    st.info(
        "💡 **Tip:** Government hospitals offer quality care at affordable rates. Premium hospitals provide faster service and additional amenities.")


def send_sms_alert(phone_number, urgent_tests, patient_name, city=""):
    """Send SMS alert for urgent medical conditions"""
    hospital_info = ""
    if city:
        hospital_info = f"\n\nNear {city}:\nConsult nearby hospitals immediately. Premium: Apollo/Manipal. Affordable: Government hospitals."

    message_body = f"""URGENT MEDICAL ALERT for {patient_name}

Critical abnormal results detected in:
{', '.join(urgent_tests)}

Please consult a healthcare provider immediately.{hospital_info}

This is an automated alert from Medical Report Analysis System."""

    if not phone_number.startswith("+91"):
        return "Invalid format - India numbers only (+91XXXXXXXXXX)"

    try:
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE,
            to=phone_number
        )
        return "SMS sent successfully"
    except Exception as e:
        return f"Failed to send: {str(e)}"
    """Send SMS alerts for urgent medical conditions"""
    message_body = f"""URGENT MEDICAL ALERT for {patient_name}

Critical abnormal results detected in:
{', '.join(urgent_tests)}

Please consult a healthcare provider immediately.

This is an automated alert from Medical Report Analysis System."""

    results = {}
    for phone in phone_numbers:
        if not phone.startswith("+91"):
            results[phone] = "Invalid format - India numbers only (+91XXXXXXXXXX)"
            continue

        try:
            message = client.messages.create(
                body=message_body,
                from_=TWILIO_PHONE,
                to=phone
            )
            results[phone] = "SMS sent successfully"
        except Exception as e:
            results[phone] = f"Failed to send: {str(e)}"

    return results


def generate_comprehensive_report_pdf(analysis, patient_name, gender="Not specified"):
    """Generate detailed PDF report with analysis and recommendations"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)

    styles = getSampleStyleSheet()
    story = []

    # Title
    title = Paragraph(f"<b>COMPREHENSIVE MEDICAL REPORT ANALYSIS</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))

    # Patient Information
    info_data = [
        ["Patient Name:", patient_name or "Not provided"],
        ["Gender:", gender],
        ["Report Date:", datetime.now().strftime("%Y-%m-%d %H:%M")],
        ["Analysis Type:", "Automated Laboratory Report Analysis"]
    ]

    info_table = Table(info_data, colWidths=[2 * inch, 3 * inch])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(info_table)
    story.append(Spacer(1, 20))

    # Results Summary
    story.append(Paragraph("<b>TEST RESULTS SUMMARY</b>", styles['Heading2']))
    story.append(Spacer(1, 12))

    # Create results table
    table_data = [["Test Name", "Result", "Reference Range", "Status"]]

    for test, data in analysis.items():
        status_color = colors.red if data['status'] in ['high', 'low'] else colors.green
        table_data.append([
            test,
            f"{data['value']} {data['unit']}",
            f"{data['range'][0]}-{data['range'][1]} {data['unit']}",
            data['status'].upper()
        ])

    results_table = Table(table_data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch, 1 * inch])
    results_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(results_table)
    story.append(Spacer(1, 20))

    # Detailed Analysis and Recommendations
    story.append(Paragraph("<b>DETAILED ANALYSIS AND RECOMMENDATIONS</b>", styles['Heading2']))
    story.append(Spacer(1, 12))

    for test, data in analysis.items():
        if data['status'] != 'normal':
            # Test header
            story.append(Paragraph(f"<b>{test}: {data['value']} {data['unit']} ({data['status'].upper()})</b>",
                                   styles['Heading3']))

            # Explanation
            story.append(Paragraph(f"<b>Clinical Significance:</b> {data['explanation']}", styles['Normal']))
            story.append(Spacer(1, 8))

            # Diet and lifestyle recommendations
            if test in DIET_PLANS and data['status'] in DIET_PLANS[test]:
                recommendations = DIET_PLANS[test][data['status']]

                if 'diet' in recommendations:
                    story.append(Paragraph("<b>Dietary Recommendations:</b>", styles['Normal']))
                    story.append(Paragraph(recommendations['diet'], styles['Normal']))
                    story.append(Spacer(1, 8))

                if 'lifestyle' in recommendations:
                    story.append(Paragraph("<b>Lifestyle Modifications:</b>", styles['Normal']))
                    story.append(Paragraph(recommendations['lifestyle'], styles['Normal']))
                    story.append(Spacer(1, 8))

                if 'warning' in recommendations:
                    story.append(Paragraph(f"<b>Important Note:</b> {recommendations['warning']}", styles['Normal']))
                    story.append(Spacer(1, 12))

            story.append(Spacer(1, 12))

    # Disclaimer
    disclaimer = """
    <b>MEDICAL DISCLAIMER:</b> This analysis is for informational purposes only and does not constitute medical advice. 
    Always consult with qualified healthcare professionals for proper medical diagnosis, treatment, and ongoing care. 
    This automated analysis should not replace professional medical consultation, especially for abnormal results.
    """
    story.append(Paragraph(disclaimer, styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer


# Main Streamlit Application
def main():
    st.set_page_config(
        page_title="Professional Medical Report Analyzer",
        page_icon="🏥",
        layout="wide"
    )

    st.title(" Professional Medical Report Analysis System")
    st.markdown("### Comprehensive Laboratory Report Analysis with Clinical Insights")
    st.markdown(
        "Upload your medical laboratory report to receive detailed analysis, clinical interpretations, and personalized health recommendations.")

    # Sidebar for patient information
    with st.sidebar:
        st.header("Patient Information")
        patient_name = st.text_input("Patient Full Name:")
        gender = st.selectbox("Gender:", ["Not specified", "male", "female"])
        patient_phone = st.text_input("Phone Number (+91XXXXXXXXXX):")
        patient_city = st.text_input("City:", placeholder="Enter your city (e.g., Mumbai, Delhi, Bangalore)")

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header(" Upload Medical Report")
        uploaded_file = st.file_uploader(
            "Choose PDF file containing your laboratory report",
            type=["pdf"],
            help="Upload a clear, text-readable PDF of your medical laboratory report"
        )

        if uploaded_file is not None:
            # Extract and analyze
            with st.spinner("Processing your medical report..."):
                text_content = extract_text_from_pdf(uploaded_file)
                extracted_values = parse_values(text_content)

            if extracted_values:
                st.success(f"Successfully extracted {len(extracted_values)} test parameters from your report")

                # Analyze results
                analysis = analyze_results(extracted_values, gender if gender != "Not specified" else "all")

                # Display results
                st.header(" Laboratory Results Analysis")

                # Summary metrics
                normal_count = sum(1 for data in analysis.values() if data['status'] == 'normal')
                abnormal_count = len(analysis) - normal_count

                metric_col1, metric_col2, metric_col3 = st.columns(3)
                with metric_col1:
                    st.metric("Total Tests", len(analysis))
                with metric_col2:
                    st.metric("Normal Results", normal_count, delta=None)
                with metric_col3:
                    st.metric("Abnormal Results", abnormal_count,
                              delta=None if abnormal_count == 0 else f"{abnormal_count} need attention")

                # Detailed results
                st.subheader(" Detailed Test Results")

                # Separate normal and abnormal results
                abnormal_results = {k: v for k, v in analysis.items() if v['status'] != 'normal'}
                normal_results = {k: v for k, v in analysis.items() if v['status'] == 'normal'}

                # Show abnormal results first if any
                if abnormal_results:
                    st.error(" ABNORMAL RESULTS REQUIRING ATTENTION")

                    for test, data in abnormal_results.items():
                        with st.expander(f" {test}: {data['value']} {data['unit']} ({data['status'].upper()})",
                                         expanded=True):
                            st.write(f"**Reference Range:** {data['range'][0]}-{data['range'][1]} {data['unit']}")
                            st.write(f"**Clinical Significance:** {data['explanation']}")

                            # Show recommendations if available
                            if test in DIET_PLANS and data['status'] in DIET_PLANS[test]:
                                recommendations = DIET_PLANS[test][data['status']]

                                if 'diet' in recommendations:
                                    st.write("** Dietary Recommendations:**")
                                    st.info(recommendations['diet'])

                                if 'lifestyle' in recommendations:
                                    st.write("** Lifestyle Modifications:**")
                                    st.info(recommendations['lifestyle'])

                                if 'warning' in recommendations:
                                    st.warning(f"**️ Important:** {recommendations['warning']}")

                # Show normal results
                if normal_results:
                    st.success(f" NORMAL RESULTS ({len(normal_results)} tests)")

                    with st.expander("View Normal Results"):
                        for test, data in normal_results.items():
                            st.write(
                                f"**{test}:** {data['value']} {data['unit']} (Range: {data['range'][0]}-{data['range'][1]} {data['unit']})")

                # Emergency SMS alerts and Hospital Recommendations
                if abnormal_results:
                    st.header("Emergency Alert System")

                    urgent_tests = list(abnormal_results.keys())

                    # Hospital recommendations
                    if patient_city:
                        display_hospital_recommendations(patient_city, urgent_tests)
                        st.markdown("---")

                    # SMS Alert section
                    st.subheader(" SMS Alert")

                    if patient_phone:
                        if st.button("Send Emergency SMS Alert", type="primary"):
                            sms_result = send_sms_alert(patient_phone, urgent_tests, patient_name or "Patient",
                                                        patient_city or "")

                            if "successfully" in sms_result:
                                st.success(f" {sms_result}")
                                if patient_city:
                                    st.info(f"SMS includes hospital recommendations for {patient_city}")
                            else:
                                st.error(f" {sms_result}")
                    else:
                        st.warning("Please provide your phone number in the sidebar to receive emergency alerts")

                    if not patient_city:
                        st.info("💡 Add your city in the sidebar to get local hospital recommendations")

                # Generate comprehensive PDF report
                st.header(" Comprehensive Report Download")

                report_buffer = generate_comprehensive_report_pdf(
                    analysis,
                    patient_name or "Anonymous Patient",
                    gender if gender != "Not specified" else "Not specified"
                )

                st.download_button(
                    label="📥 Download Complete Medical Analysis Report (PDF)",
                    data=report_buffer.getvalue(),
                    file_name=f"Medical_Analysis_Report_{patient_name or 'Patient'}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    help="Download a comprehensive PDF report with detailed analysis and recommendations"
                )

            else:
                st.warning("⚠️ No recognizable medical test values were found in the uploaded PDF. Please ensure:")
                st.write("- The PDF contains clear, readable text (not just scanned images)")
                st.write("- Laboratory test names and values are properly formatted")
                st.write("- The report contains standard medical laboratory tests")

                # Show sample of extracted text for debugging
                with st.expander("Preview extracted text (first 1000 characters)"):
                    st.text(text_content[:1000] + "..." if len(text_content) > 1000 else text_content)

    with col2:
        st.header("ℹ️ Supported Tests")
        st.markdown("""
        **Hematology:**
        - Complete Blood Count (CBC)
        - Hemoglobin, Hematocrit, RBC, WBC
        - Platelet Count, ESR

        **Biochemistry:**
        - Liver Function Tests (LFT)
        - Kidney Function Tests (KFT)
        - Lipid Profile
        - Thyroid Function Tests

        **Diabetes Markers:**
        - Blood Sugar (Fasting/Random)
        - HbA1c, Post-meal glucose

        **Vitamins & Minerals:**
        - Vitamin D, B12, Folate
        - Iron studies, Electrolytes

        **Cardiac & Inflammatory:**
        - Cardiac enzymes
        - CRP, ESR

        **Urine Analysis:**
        - Complete urine examination
        """)

        st.header("🔒 Privacy & Security")
        st.markdown("""
        - Reports processed locally
        - No data stored permanently
        - HIPAA-compliant analysis
        - Secure SMS delivery
        - Professional medical standards
        """)

        st.header(" Medical Disclaimer")
        st.warning("""
        This tool provides educational information only. 
        Always consult qualified healthcare professionals 
        for medical diagnosis and treatment. Emergency 
        medical conditions require immediate professional care.
        """)


if __name__ == "__main__":
    main()
