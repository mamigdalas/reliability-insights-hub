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

@app.route("/load_examples", methods=["POST"])
def load_examples_from_incidents():
    if 'incidents_data' not in session:
        session['incidents_data'] = []
    current_report_descriptions = [inc['Description'] for inc in session['incidents_data']]
    new_examples = [rep for rep in example_incident_reports if rep not in current_report_descriptions]
    if new_examples:
        processed_examples = automated_incident_triage(new_examples, len(session['incidents_data']))
        session['incidents_data'].extend(processed_examples)
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

    # Default dummy data for GET requests or initial load
    dummy_form_data = {
        'industry': 'Manufacturing',
        'defect_rate': 0.8,
        'on_time_delivery': 92.0,
        'customer_satisfaction': 8.5,
        'production_efficiency': 85.0,
        'employee_turnover': 10.0,
        'patient_wait_time': 20.0,
        'bed_occupancy': 75.0
    }

    current_dummy_form_data = dummy_form_data.copy()

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

        # Update dummy data with submitted form values for persistence
        current_dummy_form_data.update(request.form)

        selected_industry_benchmarks = BENCHMARKS.get(user_metrics['industry'], {})

        comparison_results_list = []
        bar_chart_data = []

        lower_is_better_metrics = ["Defect Rate (%)", "Employee Turnover (%)", "Patient Wait Time (min)"]

        for metric, user_value in user_metrics.items():
            if metric == "industry": continue

            industry_best = selected_industry_benchmarks.get("Industry Best", {}).get(metric)
            world_class_best = selected_industry_benchmarks.get("World-Class Functional Best", {}).get(metric)

            if industry_best is not None and world_class_best is not None:
                is_higher_better = metric not in lower_is_better_metrics

                gap_to_industry = 0
                gap_to_world_class = 0

                if is_higher_better:
                    if industry_best > 0: # Avoid division by zero
                        gap_to_industry = ((industry_best - user_value) / industry_best) * 100
                    if world_class_best > 0:
                        gap_to_world_class = ((world_class_best - user_value) / world_class_best) * 100
                else: # Lower is better
                    if industry_best > 0: # Avoid division by zero
                        gap_to_industry = ((user_value - industry_best) / industry_best) * 100
                    if world_class_best > 0:
                        gap_to_world_class = ((user_value - world_class_best) / world_class_best) * 100

                comparison_results_list.append({
                    'Metric': metric,
                    'Your Value': user_value,
                    'Industry Best': industry_best,
                    'World-Class Best': world_class_best,
                    'Gap to Industry (%)': round(gap_to_industry, 2),
                    'Gap to World-Class (%)': round(gap_to_world_class, 2),
                    'Is_Higher_Better': is_higher_better
                })

        comparison_results = comparison_results_list # Update the outer variable

        # Generate advice
        advice.append(f"Analyzing your performance against the '{user_metrics['industry']}' industry:")
        for res in comparison_results:
            metric = res['Metric']
            your_val = res['Your Value']
            industry_val = res['Industry Best']
            world_val = res['World-Class Best']
            gap_industry_pc = res['Gap to Industry (%)']
            is_higher_better = res['Is_Higher_Better']

            if is_higher_better:
                if your_val >= world_val:
                    advice.append(f" - **{metric}**: Your performance ({your_val}%) is world-class! Excellent work. Maintain these standards.")
                elif your_val >= industry_val:
                    advice.append(f" - **{metric}**: Your performance ({your_val}%) exceeds industry best. Focus on continuous improvement to reach world-class levels.")
                else:
                    advice.append(f" - **{metric}**: Your performance ({your_val}%) is below industry best (Avg: {industry_val}%). Focus on strategies to improve this metric. (Gap: {abs(gap_industry_pc)}%)")
            else: # Lower is better
                if your_val <= world_val:
                    advice.append(f" - **{metric}**: Your performance ({your_val}%) is world-class! Excellent work. Maintain these low levels of deviation.")
                elif your_val <= industry_val:
                    advice.append(f" - **{metric}**: Your performance ({your_val}%) is better than industry best. Continue to optimize. (Gap: {abs(gap_industry_pc)}%)")
                else:
                    advice.append(f" - **{metric}**: Your performance ({your_val}%) is above industry best (Avg: {industry_val}%). Implement measures to reduce this metric. (Gap: {abs(gap_industry_pc)}%)")

        # Generate Plotly Chart
        df_results_plot = pd.DataFrame(comparison_results)
        fig = go.Figure()

        fig.add_trace(go.Bar(
            name='Your Value',
            x=df_results_plot['Metric'],
            y=df_results_plot['Your Value'],
            marker_color='indianred'
        ))
        fig.add_trace(go.Bar(
            name='Industry Best',
            x=df_results_plot['Metric'],
            y=df_results_plot['Industry Best'],
            marker_color='lightsalmon'
        ))
        fig.add_trace(go.Bar(
            name='World-Class Best',
            x=df_results_plot['Metric'],
            y=df_results_plot['World-Class Best'],
            marker_color='lightskyblue'
        ))

        fig.update_layout(barmode='group', title_text='Performance Benchmarking', yaxis_title='Value (%) or Score')
        plot_data = json.loads(fig.to_json())

    # This ensures a render_template call always happens, even for GET requests
    return render_template(
        'benchmarking.html',
        active_page='benchmarking',
        benchmarks_info=BENCHMARKS,
        dummy_form_data=current_dummy_form_data,
        comparison_results=comparison_results,
        plot_data=plot_data,
        advice=advice
    )


@app.route('/routines', methods=['GET', 'POST'])
def routines_page():
    routine_analysis_results = None
    routine_advice = []
    ideal_routine_input = ""
    actual_routine_input = ""

    if request.method == 'POST':
        ideal_routine_str = request.form['ideal_routine']
        actual_routine_str = request.form['actual_routine']

        ideal_routine_input = ideal_routine_str
        actual_routine_input = actual_routine_str

        ideal_steps = [s.strip() for s in ideal_routine_str.split(',') if s.strip()]
        actual_steps = [s.strip() for s in actual_routine_str.split(',') if s.strip()]

        routine_analysis_results = []
        max_len = max(len(ideal_steps), len(actual_steps))

        deviations = {
            'omitted': [],
            'added': [],
            'reordered': []
        }

        # Simple comparison for analysis results and initial deviation check
        for i in range(max_len):
            ideal_step = ideal_steps[i] if i < len(ideal_steps) else "N/A"
            actual_step = actual_steps[i] if i < len(actual_steps) else "N/A"

            status = "Match"
            if ideal_step == actual_step:
                status = "Match"
            elif ideal_step == "N/A":
                status = "Added Step"
                deviations['added'].append(actual_step)
            elif actual_step == "N/A":
                status = "Omitted Step"
                deviations['omitted'].append(ideal_step)
            else:
                status = "Deviation"
                if actual_step not in ideal_steps:
                    deviations['added'].append(actual_step)
                if ideal_step not in actual_steps:
                    deviations['omitted'].append(ideal_step)

            routine_analysis_results.append({
                'Step_Number': i + 1,
                'Ideal_Step': ideal_step,
                'Actual_Step': actual_step,
                'Status': status
            })

        # More refined deviation analysis for advice
        omitted_steps = set(ideal_steps) - set(actual_steps)
        added_steps = set(actual_steps) - set(ideal_steps)

        reordered = False
        if len(ideal_steps) == len(actual_steps) and omitted_steps == set() and added_steps == set():
            if ideal_steps != actual_steps:
                reordered = True

        if not omitted_steps and not added_steps and not reordered:
            routine_advice.append("Excellent! Your actual routine closely matches the ideal routine. This indicates strong process adherence and predictability.")
        else:
            if omitted_steps:
                routine_advice.append(f"Omitted Steps: The following ideal steps were not performed: {', '.join(omitted_steps)}. This could indicate shortcuts or a lack of understanding of critical steps.")
            if added_steps:
                routine_advice.append(f"Added Steps: The following steps were performed but are not in the ideal routine: {', '.join(added_steps)}. This might indicate workarounds, unapproved procedures, or necessary adjustments that should be formalized.")
            if reordered:
                routine_advice.append("Reordered Steps: The sequence of steps has changed. While all steps might be present, an altered order can introduce new risks or inefficiencies.")

            routine_advice.append("Action: Investigate the reasons for these deviations. Are ideal routines practical? Is training sufficient? Are there unspoken norms (workarounds) that need to be addressed?")

    return render_template(
        'routines.html',
        active_page='routines',
        ideal_routine_input=ideal_routine_input,
        actual_routine_input=actual_routine_input,
        routine_analysis_results=routine_analysis_results,
        routine_advice=routine_advice
    )


if __name__ == '__main__':
    app.run(debug=True)
    @app.route("/", methods=["GET", "POST"])
def incident_analyzer_page():
    # ... existing code ...

    if request.method == "POST":
        if 'incident_description' in request.form:
            new_report = request.form['incident_description']
            if new_report.strip():
                processed_new_report = automated_incident_triage([new_report], len(session['incidents_data']))
                session['incidents_data'].extend(processed_new_report)
                print(f"DEBUG: Incident added. Current session data: {session['incidents_data']}") # <-- ADD THIS LINE

        return redirect(url_for('incident_analyzer_page'))
    # ... rest of the code ...
