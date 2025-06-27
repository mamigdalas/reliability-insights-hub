import os
from flask import Flask, render_template, request, session, redirect, url_for
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json

app = Flask(__name__)
# IMPORTANT: For production, set a strong secret key via environment variable.
# For development and Render's free tier, a hardcoded one is okay for testing,
# but know this is a security risk for sensitive applications.
app.secret_key = os.environ.get('SECRET_KEY', 'a_very_secret_key_for_seminar_app')

# --- Incident Analysis Logic (From Day 2 Project) ---
def automated_incident_triage(incident_reports, current_total_incidents):
    """
    Analyzes a list of incident reports, categorizes them,
    suggests potential root cause hints, and action priorities.
    """
    keywords = {
        "Equipment Failure": ["malfunction", "faulty", "broke", "failure", "mechanical", "electrical", "sensor", "pump", "valve", "engine"],
        "Human Error": ["mistake", "forgot", "misread", "missed", "oversight", "operator", "crew", "training", "procedure deviation", "communication breakdown"],
        "Procedure/Process Issue": ["procedure", "protocol", "checklist", "SOP", "unclear", "ambiguous", "outdated", "steps", "process flow", "workflow"],
        "Environmental Factor": ["weather", "rain", "wind", "slippery", "lighting", "visibility", "temperature", "noise", "vibration"],
        "Maintenance Related": ["maintenance", "repair", "inspection", "servicing", "worn", "scheduled"],
        "Communication Breakdown": ["communication", "handover", "briefing", "missed call", "misunderstood"]
    }

    action_suggestions = {
        "Equipment Failure": "Schedule immediate inspection and maintenance; review equipment history.",
        "Human Error": "Review training protocols; conduct task analysis; consider human factors study.",
        "Procedure/Process Issue": "Initiate procedure review; update documentation; conduct process walkthrough.",
        "Environmental Factor": "Assess environmental controls; update site safety plans; provide awareness training.",
        "Maintenance Related": "Evaluate maintenance schedule/quality; review spare parts inventory.",
        "Communication Breakdown": "Implement new communication protocols; conduct handover training; review briefing methods.",
        "General Investigation": "Conduct full root cause analysis (RCA) to understand contributing factors."
    }

    processed_reports = []
    # Use current_total_incidents for ID generation to ensure uniqueness across sessions
    start_id = current_total_incidents + 1

    for i, report in enumerate(incident_reports):
        report_lower = report.lower()
        detected_categories = []
        inferred_action = "Investigate Further" # Default action

        severity = "Low"
        if any(s_kw in report_lower for s_kw in ["severe", "major", "critical", "injury", "fatality", "shutdown"]):
            severity = "High"
        elif any(m_kw in report_lower for m_kw in ["minor", "small", "limited disruption"]):
            severity = "Medium"

        for category, kws in keywords.items():
            if any(kw in report_lower for kw in kws):
                detected_categories.append(category)

        # Simple logic to determine the primary inferred action based on detected categories
        if "Equipment Failure" in detected_categories:
            inferred_action = action_suggestions["Equipment Failure"]
        elif "Procedure/Process Issue" in detected_categories:
            inferred_action = action_suggestions["Procedure/Process Issue"]
        elif "Human Error" in detected_categories:
            inferred_action = action_suggestions["Human Error"]
        elif "Environmental Factor" in detected_categories:
            inferred_action = action_suggestions["Environmental Factor"]
        elif "Maintenance Related" in detected_categories:
            inferred_action = action_suggestions["Maintenance Related"]
        elif "Communication Breakdown" in detected_categories:
            inferred_action = action_suggestions["Communication Breakdown"]
        else:
            inferred_action = action_suggestions["General Investigation"]

        processed_reports.append({
            "Report_ID": f"INC-{start_id + i:03d}",
            "Description": report,
            "Severity": severity,
            "Inferred_Categories": ", ".join(detected_categories) if detected_categories else "Unknown",
            "Suggested_Action": inferred_action
        })
    return processed_reports

# Example incident reports
example_incident_reports = [
    "Operator failed to follow procedure for lockout/tagout, leading to unexpected equipment startup. Minor injury sustained.",
    "Sudden power surge caused critical pump malfunction. No immediate harm, but production halted for 2 hours.",
    "Communication breakdown during shift handover led to a missed critical safety check on Valve 3.",
    "Routine inspection found severe corrosion on main support beam due to faulty coating application 5 years ago. Potential for collapse.",
    "New trainee misread pressure gauge, resulting in minor overpressure in the system. No damage.",
    "Slippery floor near west entrance due to unexpected rain caused a slip and fall incident. No injury.",
    "Automated sensor for temperature control malfunctioned, causing product to overheat. Scrap material.",
    "Team forgot to perform the pre-operation checklist as per protocol, minor valve leak detected afterwards.",
    "Procedure for hazardous waste disposal is ambiguous, leading to different interpretations by staff.",
    "High winds caused unsecured scaffolding to partially collapse. No personnel injured, but significant structural damage.",
    "A critical engine component failed mid-flight, forcing an emergency landing. All passengers safe. Major incident.",
    "Regular maintenance on conveyor belt was delayed due to parts shortage, leading to unexpected stoppage and production delay.",
    "Overnight crew did not properly brief day crew on critical equipment status. Misunderstanding led to a near-miss collision.",
    "Faulty wiring in the control panel caused intermittent system errors, impacting data integrity. Minor issue, but frequent.",
    "New safety protocol for confined spaces is very unclear, leading to confusion among operators and delays."
]

@app.route("/", methods=["GET", "POST"])
def incident_analyzer_page():
    analysis_results = []
    plot_data = None
    high_severity_count = 0

    if 'incidents_data' not in session:
        session['incidents_data'] = []

    if request.method == "POST":
        if 'incident_description' in request.form:
            new_report = request.form['incident_description']
            if new_report.strip(): # Only process non-empty descriptions
                # Pass the current total number of incidents for unique ID generation
                processed_new_report = automated_incident_triage([new_report], len(session['incidents_data']))
                session['incidents_data'].extend(processed_new_report)
        elif 'load_examples' in request.form:
            current_report_descriptions = [inc['Description'] for inc in session['incidents_data']]
            new_examples = [rep for rep in example_incident_reports if rep not in current_report_descriptions]
            if new_examples:
                processed_examples = automated_incident_triage(new_examples, len(session['incidents_data']))
                session['incidents_data'].extend(processed_examples)
        
        # After any POST request that modifies session data, redirect to GET to prevent form re-submission issues
        return redirect(url_for('incident_analyzer_page'))

    # Logic for GET requests and after redirect
    if session['incidents_data']:
        analysis_results = session['incidents_data']
        df_results = pd.DataFrame(analysis_results)

        # Generate Plotly charts
        # Severity Chart
        severity_counts = df_results['Severity'].value_counts().reindex(['High', 'Medium', 'Low'], fill_value=0)
        severity_fig = go.Figure(data=[go.Bar(x=severity_counts.index, y=severity_counts.values,
                                             marker_color=['#dc3545', '#ffc107', '#28a745'])]) # Bootstrap colors
        severity_fig.update_layout(title_text='Incidents by Severity', showlegend=False,
                                   margin=dict(l=20, r=20, t=40, b=20))


        # Category Chart
        all_categories = df_results['Inferred_Categories'].str.split(', ').explode().str.strip()
        filtered_categories = all_categories[all_categories != 'Unknown']
        category_counts = filtered_categories.value_counts()
        # Ensure there's data for pie chart
        if not category_counts.empty:
            category_fig = go.Figure(data=[go.Pie(labels=category_counts.index, values=category_counts.values, hole=.3)])
            category_fig.update_layout(title_text='Incidents by Inferred Category', showlegend=True,
                                       margin=dict(l=20, r=20, t=40, b=20))
        else:
            # Create an empty figure or a placeholder if no categories are present
            category_fig = go.Figure().update_layout(title_text='No Category Data Yet')

        plot_data = {
            'severity_data': severity_fig.to_json(pretty=False),
            'category_data': category_fig.to_json(pretty=False)
        }
        # In Plotly, .data and .layout are already part of the figure object itself
        # We pass the full figure as JSON to the template.

        high_severity_count = df_results[df_results['Severity'] == 'High'].shape[0]

    return render_template("incident_analyzer.html", analysis_results=analysis_results,
                           incidents=session['incidents_data'], plot_data=plot_data,
                           high_severity_count=high_severity_count)

if __name__ == '__main__':
    # When deploying to Render, the 'PORT' environment variable will be set by Render.
    # Locally, it will default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)