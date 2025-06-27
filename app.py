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

### NEW SECTION FOR BENCHMARKING MODULE ###

# Dummy data for industry and world-class benchmarks (simulated for simplicity)
# These are illustrative targets.
BENCHMARKS = {
    "Manufacturing": {
        "Industry Best": {
            "Defect Rate (%)": 0.5,
            "On-Time Delivery (%)": 95,
            "Customer Satisfaction (Score)": 8.5,
            "Production Efficiency (%)": 80
        },
        "World-Class Functional Best": {
            "Defect Rate (%)": 0.01,  # From e.g., electronics manufacturing
            "On-Time Delivery (%)": 99, # From e.g., logistics
            "Customer Satisfaction (Score)": 9.5, # From e.g., service industries
            "Production Efficiency (%)": 95 # From e.g., lean automotive
        }
    },
    "Service": {
        "Industry Best": {
            "Defect Rate (%)": 0.2, # E.g., errors in service delivery
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
            "Defect Rate (%)": 0.8, # E.g., medical errors
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
        # Extract user inputs
        user_metrics = {
            "industry": request.form['industry'],
            "Defect Rate (%)": float(request.form['defect_rate']),
            "On-Time Delivery (%)": float(request.form['on_time_delivery']),
            "Customer Satisfaction (Score)": float(request.form['customer_satisfaction']),
            # Handle other metrics based on selected industry or provide defaults
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

                # Define if higher/lower is better for each metric
                is_higher_better = ("%" in metric and "Defect" not in metric and "Turnover" not in metric and "Wait" not in metric) or ("Score" in metric)

                # Calculate percentage gap relative to the benchmark
                if is_higher_better:
                    industry_gap_pct = ((industry_best - user_value) / industry_best) * 100 if industry_best != 0 else 0
                    world_class_gap_pct = ((world_class_best - user_value) / world_class_best) * 100 if world_class_best != 0 else 0
                else: # Lower is better (Defect Rate, Turnover, Wait Time)
                    industry_gap_pct = ((user_value - industry_best) / industry_best) * 100 if industry_best != 0 else 0
                    world_class_gap_pct = ((user_value - world_class_best) / world_class_best) * 100 if world_class_best != 0 else 0

                comparison_results_list.append({
                    "Metric": metric,
                    "Your Value": user_value,
                    "Industry Best": industry_best,
                    "World-Class Best": world_class_best,
                    "Gap to Industry (%)": round(industry_gap_pct, 2),
                    "Gap to World-Class (%)": round(world_class_gap_pct, 2),
                    "Is_Higher_Better": is_higher_better
                })

                # Prepare data for bar chart
                bar_chart_data.append(
                    go.Bar(name='Your Value', x=[metric], y=[user_value], marker_color='#0056b3'),
                )
                bar_chart_data.append(
                    go.Bar(name='Industry Best', x=[metric], y=[industry_best], marker_color='#ffc107'),
                )
                bar_chart_data.append(
                    go.Bar(name='World-Class Best', x=[metric], y=[world_class_best], marker_color='#28a745'),
                )

        if comparison_results_list:
            df_comparison = pd.DataFrame(comparison_results_list)
            comparison_results = df_comparison.to_dict(orient='records') # Convert back to list of dicts for template

            # Generate Plotly comparison chart
            fig = go.Figure(data=bar_chart_data)
            fig.update_layout(barmode='group', title_text='Performance Benchmarking Comparison',
                              margin=dict(l=20, r=20, t=40, b=20))
            plot_data = fig.to_json(pretty=False)

            # Generate advice
            advice.append("Benchmarking is crucial for **Preoccupation with Failure** – actively seeking out weaknesses and areas for improvement before they manifest as failures.")
            for res in comparison_results_list:
                if res["Is_Higher_Better"]:
                    if res["Gap to Industry (%)"] > 0:
                        advice.append(f"Your {res['Metric']} is {res['Gap to Industry (%)']:.2f}% below Industry Best. This indicates a competitive gap. Consider **Competitive Benchmarking** focused on internal operational improvements related to {res['Metric']}.")
                    if res["Gap to World-Class (%)"] > 0:
                        advice.append(f"Your {res['Metric']} is {res['Gap to World-Class (%)']:.2f}% below World-Class Best. This suggests a functional gap. Explore **Functional Benchmarking** with leading organizations in *any* industry excellent at {res['Metric']} (e.g., logistics for On-Time Delivery).")
                else: # Lower is better
                    if res["Gap to Industry (%)"] > 0: # User's value is higher than industry best (worse)
                        advice.append(f"Your {res['Metric']} is {res['Gap to Industry (%)']:.2f}% higher than Industry Best. This indicates a competitive gap. Consider **Competitive Benchmarking** focused on internal operational improvements related to {res['Metric']}.")
                    if res["Gap to World-Class (%)"] > 0: # User's value is higher than world-class best (worse)
                        advice.append(f"Your {res['Metric']} is {res['Gap to World-Class (%)']:.2f}% higher than World-Class Best. This suggests a functional gap. Explore **Functional Benchmarking** with leading organizations in *any* industry excellent at {res['Metric']} (e.g., hospitals for reducing wait times).")

        session['benchmarking_results'] = comparison_results # Store results in session if needed later
        session['benchmarking_plot_data'] = plot_data
        session['benchmarking_advice'] = advice

        return redirect(url_for('benchmarking_page')) # Redirect after POST

    # On GET request, load data from session if available
    if 'benchmarking_results' in session:
        comparison_results = session['benchmarking_results']
        plot_data = session['benchmarking_plot_data']
        advice = session['benchmarking_advice']

    # Pass dummy data if no POST yet for initial form load
    dummy_form_data = {
        "industry": "Manufacturing",
        "defect_rate": 1.0,
        "on_time_delivery": 90.0,
        "customer_satisfaction": 7.5,
        "production_efficiency": 70.0,
        "employee_turnover": 20.0,
        "patient_wait_time": 45.0,
        "bed_occupancy": 80.0
    }

    return render_template("benchmarking.html",
                           user_metrics=user_metrics,
                           comparison_results=comparison_results,
                           plot_data=plot_data,
                           advice=advice,
                           benchmarks_info=BENCHMARKS,
                           dummy_form_data=dummy_form_data,
                           active_page='benchmarking')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)