def assess_symptoms(symptoms: list) -> dict:
    """
    Simple rule-based triage engine.
    """
    symptoms = [s.lower().strip() for s in symptoms]

    high_risk = {'chest pain', 'difficulty breathing', 'severe bleeding', 'unconscious', 'seizure'}
    medium_risk = {'high fever', 'persistent vomiting', 'severe headache', 'dehydration'}
    low_risk = {'mild fever', 'cough', 'cold', 'headache', 'body ache'}

    if any(s in high_risk for s in symptoms):
        return {
            'urgency': 'HIGH',
            'message': 'Please seek emergency medical attention immediately.',
            'recommendation': 'Visit nearest hospital emergency room now.'
        }
    elif any(s in medium_risk for s in symptoms):
        return {
            'urgency': 'MEDIUM',
            'message': 'You should consult a doctor soon.',
            'recommendation': 'Visit a nearby clinic within 24 hours.'
        }
    elif any(s in low_risk for s in symptoms):
        return {
            'urgency': 'LOW',
            'message': 'Your symptoms seem mild.',
            'recommendation': 'Rest, stay hydrated. Monitor symptoms for 2-3 days.'
        }
    else:
        return {
            'urgency': 'UNKNOWN',
            'message': 'Unable to assess these symptoms confidently.',
            'recommendation': 'Please consult a healthcare professional for accurate diagnosis.'
        }
