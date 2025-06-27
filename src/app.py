import os
from flask import Flask, render_template, request, session, redirect, url_for
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'a_very_secret_key_for_seminar_app')

# --- Incident Analysis Logic (From Day 2 Project) ---
def automated_incident_triage(incident_reports, current_total_incidents):
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
            if new_report.strip():
                processed_new_report = automated_incident_triage([new_report], len(session['incidents_data']))
                session['incidents_data'].extend(processed_new_report)
        elif 'load_examples' in request.form:
            current_report_descriptions = [inc['Description'] for inc in session['incidents_data']]
            new_examples = [rep for rep in example_incident_reports if rep not in current_report_descriptions]
            if new_examples:
                processed_examples = automated_incident_triage(new_examples, len(session['incidents_data']))
                session['incidents_data'].extend(processed_examples)

        return redirect(url_for('incident_analyzer_page'))

    if session['incidents_data']:
        analysis_results = session['incidents_data']
        df_results = pd.DataFrame(analysis_results)

        severity_counts = df_results['Severity'].value_counts().reindex(['High', 'Medium', 'Low'], fill_value=0)
        severity_fig = go.Figure(data=[go.Bar(x=severity_counts.index, y=severity_counts.values,
                                             marker_color=['#dc3545', '#ffc107', '#28a745'])])
        severity_fig.update_layout(title_text='Incidents by Severity', showlegend=False,
                                   margin=dict(l=20, r=20, t=40, b=20))

        all_categories = df_results['Inferred_Categories'].str.split(', ').explode().str.strip()
        filtered_categories = all_categories[all_categories != 'Unknown']
        category_counts = filtered_categories.value_counts()

        if not category_counts.empty:
            category_fig = go.Figure(data=[go.Pie(labels=category_counts.index, values=category_counts.values, hole=.3)])
            category_fig.update_layout(title_text='Incidents by Inferred Category', showlegend=True,
                                       margin=dict(l=20, r=20, t=40, b=20))
        else:
            category_fig = go.Figure().update_layout(title_text='No Category Data Yet')

        plot_data = {
            'severity_data': severity_fig.to_json(pretty=False),
            'category_data': category_fig.to_json(pretty=False)
        }

        high_severity_count = df_results[df_results['Severity'] == 'High'].shape[0]

    return render_template("incident_analyzer.html", analysis_results=analysis_results,
                           incidents=session['incidents_data'], plot_data=plot_data,
                           high_severity_count=high_severity_count, active_page='incidents')

@app.route("/clear_incidents", methods=["POST"])
def clear_incidents():
    session['incidents_data'] = []
    return redirect(url_for('incident_analyzer_page'))

# --- Benchmarking Logic (From Day 3 Project) ---
BENCHMARKS = {
    "Manufacturing": {
        "Industry Best": {
            "Defect Rate (%)": 0.5,
            "On-Time Delivery (%)": 95,
            "Customer Satisfaction (Score)": 8.5,
            "Production Efficiency (%)": 80
        },
        "World-Class Functional Best": {
            "Defect Rate (%)": 0.01,
            "On-Time Delivery (%)": 99,
            "Customer Satisfaction (Score)": 9.5,
            "Production Efficiency (%)": 95
        }
    },
    "Service": {
        "Industry Best": {
            "Defect Rate (%)": 0.2,
            "On-Time Delivery (%)": 90,
            "Customer Satisfaction (Score)": 8.8,
            "Employee Turnover (%)": 15
        },
        "World-Class Functional Best": {
            "Defect Rate (%)": 0.05,
            "On-Time Delivery (%)": 98,
            "Customer Satisfaction (Score)": 9.8,
            "Employee Turnover (%)": 5
        }
    },
    "Healthcare": {
        "Industry Best": {
            "Defect Rate (%)": 0.8,
            "Patient Wait Time (min)": 30,
            "Patient Satisfaction (Score)": 8.0,
            "Bed Occupancy (%)": 85
        },
        "World-Class Functional Best": {
            "Defect Rate (%)": 0.1,
            "Patient Wait Time (min)": 5,
            "Patient Satisfaction (Score)": 9.5,
            "Bed Occupancy (%)": 98
        }
    }
}

@app.route("/benchmarking", methods=["GET", "POST"])
def benchmarking_page():
    user_metrics = {}
    comparison_results = []
    plot_data = None
    advice = []

    if request.method == "POST":
        user_metrics = {
            "industry": request.form['industry'],
            "Defect Rate (%)": float(request.form['defect_rate']),
            "On-Time Delivery (%)": float(request.form['on_time_delivery']),
            "Customer Satisfaction (Score)": float(request.form['customer_satisfaction']),
        }
        if user_metrics["industry"] == "Manufacturing":
             user_metrics["Production Efficiency (%)"] = float(request.form['production_efficiency'])
        elif user_metrics["industry"] == "Service":
             user_metrics["Employee Turnover (%)"] = float(request.form['employee_turnover'])
        elif user_metrics["industry"] == "Healthcare":
             user_metrics["Patient Wait Time (min)"] = float(request.form['patient_wait_time'])
             user_metrics["Bed Occupancy (%)"] = float(request.form['bed_occupancy'])


        selected_industry_benchmarks = BENCHMARKS.get(user_metrics['industry'], {})

        comparison_results_list = []
        bar_chart_data = []

        for metric, user_value in user_metrics.items():
            if metric == "industry": continue

            industry_best = selected_industry_benchmarks.get("Industry Best", {}).get(metric)
            world_class_best = selected_industry_benchmarks.get("World-Class Functional Best", {}).get(metric)

            if industry_best is not None and world_class_best is not None:
                gap_industry = user_value - industry_best
                gap_world_class = user_value - world_class_best

                is_higher_