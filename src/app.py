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
        "Equipment Failure": "Schedule immediate inspection and maintenance; review equipment history for recurring issues.",
        "Human Error": "Initiate procedure review; update documentation; conduct process walkthrough; provide targeted training.",
        "Procedure/Process Issue": "Revise and simplify relevant procedures; implement stricter adherence checks; conduct process mapping.",
        "Environmental Factor": "Develop contingency plans for adverse conditions; implement environmental monitoring systems.",
        "Maintenance Related": "Implement predictive maintenance techniques; optimize maintenance schedules; conduct component-level failure analysis.",
        "Communication Breakdown": "Establish clear communication protocols; implement read-back/verify procedures; improve shift handover processes."
    }

    processed_reports = []
    start_id = current_total_incidents + 1
    for i, report in enumerate(incident_reports):
        inferred_categories = []
        for category, kws in keywords.items():
            if any(kw in report.lower() for kw in kws):
                inferred_categories.append(category)

        if not inferred_categories:
            inferred_categories.append("Unknown")

        # Simplified severity assignment for demonstration
        severity = "Low"
        if "major" in report.lower() or "critical" in report.lower() or "shutdown" in report.lower():
            severity = "High"
        elif "minor" in report.lower() or "small" in report.lower():
            severity = "Low"
        else:
            severity = "Medium" # Default if no specific keywords

        # Suggest action based on the first inferred category or a default
        suggested_action = action_suggestions.get(inferred_categories[0], "Conduct full root cause analysis (RCA) to understand contributing factors.")

        processed_reports.append({
            "Report_ID": f"INC-{start_id + i:03d}",
            "Description": report,
            "Severity": severity,
            "Inferred_Categories": ", ".join(inferred_categories),
            "Suggested_Action": suggested_action
        })
    return processed_reports

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
                print(f"DEBUG: Incident added. Current session data: {session['incidents_data']}")
        elif 'clear_all_incidents' in request.form:
            session['incidents_data'] = []
            return redirect(url_for('incident_analyzer_page'))

    if session['incidents_data']:
        df = pd.DataFrame(session['incidents_data'])

        # Aggregate data for Plotly charts
        severity_counts = df['Severity'].value_counts().reindex(["Low", "Medium", "High"]).fillna(0)
        category_counts = df['Inferred_Categories'].str.get_dummies(sep=', ').sum().sort_values(ascending=False)

        # Severity Distribution Chart
        severity_fig = go.Figure(data=[go.Pie(labels=severity_counts.index, values=severity_counts.values, hole=.3)])
        severity_fig.update_layout(title_text='Incident Severity Distribution', title_x=0.5)

        # Category Distribution Chart (Bar Chart)
        category_fig = go.Figure(data=[go.Bar(x=category_counts.index, y=category_counts.values)])
        category_fig.update_layout(title_text='Incident Category Distribution', title_x=0.5,
                                    xaxis_title="Category", yaxis_title="Number of Incidents")

        plot_data = {
            'severity_data': severity_fig.to_json(),
            'category_data': category_fig.to_json()
        }

        # Calculate high severity count for alert
        high_severity_count = df[df['Severity'] == 'High'].shape[0]

    return render_template("incident_analyzer.html", analysis_results=session['incidents_data'], plot_data=plot_data, high_severity_count=high_severity_count)

# --- Performance Benchmarker Logic (From Day 3 Project) ---
BENCHMARKS = {
    "Manufacturing": {
        "Industry Best": {
            "Safety Incidents (TRIR)": 0.5,
            "Quality Defects (PPM)": 100,
            "Maintenance Costs (% of Revenue)": 2.0,
            "Overall Equipment Effectiveness (OEE) (%)": 85.0,
            "Energy Consumption (kWh/unit)": 1.5,
            "Defect Rate (%)": 0.5,
            "On-Time Delivery (%)": 98.0,
            "Customer Satisfaction (Score)": 4.5,
            "Production Efficiency (%)": 90.0 # Specific to Manufacturing
        },
        "World-Class Functional Best": {
            "Safety Incidents (TRIR)": 0.1,
            "Quality Defects (PPM)": 10,
            "Maintenance Costs (% of Revenue)": 0.5,
            "Overall Equipment Effectiveness (OEE) (%)": 95.0,
            "Energy Consumption (kWh/unit)": 0.8,
            "Defect Rate (%)": 0.1,
            "On-Time Delivery (%)": 99.9,
            "Customer Satisfaction (Score)": 4.9,
            "Production Efficiency (%)": 98.0 # Specific to Manufacturing
        }
    },
    "Service": {
        "Industry Best": {
            "Safety Incidents (TRIR)": 0.8,
            "Quality Defects (PPM)": 50, # Reinterpreted as Service Errors per Million Interactions
            "Maintenance Costs (% of Revenue)": 1.0, # IT/Facility maintenance relevant
            "Overall Equipment Effectiveness (OEE) (%)": 90.0, # System uptime/availability
            "Energy Consumption (kWh/unit)": 0.7, # Per service unit or transaction
            "Defect Rate (%)": 0.1, # Service error rate
            "On-Time Delivery (%)": 95.0, # Service delivery timeliness
            "Customer Satisfaction (Score)": 4.2,
            "Employee Turnover (%)": 15.0 # Specific to Service
        },
        "World-Class Functional Best": {
            "Safety Incidents (TRIR)": 0.2,
            "Quality Defects (PPM)": 5,
            "Maintenance Costs (% of Revenue)": 0.2,
            "Overall Equipment Effectiveness (OEE) (%)": 99.5,
            "Energy Consumption (kWh/unit)": 0.3,
            "Defect Rate (%)": 0.01,
            "On-Time Delivery (%)": 99.0,
            "Customer Satisfaction (Score)": 4.8,
            "Employee Turnover (%)": 5.0 # Specific to Service
        }
    },
    "Healthcare": {
        "Industry Best": {
            "Safety Incidents (TRIR)": 1.2, # Staff safety incidents
            "Quality Defects (PPM)": 200, # Medical errors per patient interactions
            "Maintenance Costs (% of Revenue)": 3.0, # Medical equipment/facility
            "Overall Equipment Effectiveness (OEE) (%)": 80.0, # Medical device uptime
            "Energy Consumption (kWh/unit)": 2.0, # Per bed or patient day
            "Defect Rate (%)": 1.0, # Hospital acquired infection rate or readmission
            "On-Time Delivery (%)": 90.0, # Timeliness of patient care
            "Customer Satisfaction (Score)": 3.8, # Patient satisfaction
            "Patient Wait Time (min)": 30.0, # Specific to Healthcare
            "Bed Occupancy (%)": 85.0 # Specific to Healthcare
        },
        "World-Class Functional Best": {
            "Safety Incidents (TRIR)": 0.3,
            "Quality Defects (PPM)": 20,
            "Maintenance Costs (% of Revenue)": 1.0,
            "Overall Equipment Effectiveness (OEE) (%)": 90.0,
            "Energy Consumption (kWh/unit)": 1.0,
            "Defect Rate (%)": 0.2,
            "On-Time Delivery (%)": 98.0,
            "Customer Satisfaction (Score)": 4.7,
            "Patient Wait Time (min)": 10.0,
            "Bed Occupancy (%)": 95.0
        }
    }
}

@app.route("/benchmarking", methods=["GET", "POST"])
def benchmarking_page():
    comparison_results_list = []
    plot_data = None
    if request.method == "POST":
        user_metrics = {
            "industry": request.form['industrySelect'],
            "Safety Incidents (TRIR)": float(request.form['safety_incidents']),
            "Quality Defects (PPM)": float(request.form['quality_defects']),
            "Maintenance Costs (% of Revenue)": float(request.form['maintenance_costs']),
            "Overall Equipment Effectiveness (OEE) (%)": float(request.form['oee']),
            "Energy Consumption (kWh/unit)": float(request.form['energy_consumption']),
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

        bar_chart_data = []

        for metric, user_value in user_metrics.items():
            if metric == "industry": continue

            industry_best = selected_industry_benchmarks.get("Industry Best", {}).get(metric)
            world_class_best = selected_industry_benchmarks.get("World-Class Functional Best", {}).get(metric)

            if industry_best is not None and world_class_best is not None:
                gap_industry = user_value - industry_best
                gap_world_class = user_value - world_class_best
                status_industry = "Below" if gap_industry > 0 else ("At Par" if gap_industry == 0 else "Above")
                status_world_class = "Below" if gap_world_class > 0 else ("At Par" if gap_world_class == 0 else "Above")

                comparison_results_list.append({
                    "Metric": metric,
                    "Your Value": user_value,
                    "Industry Best": industry_best,
                    "World-Class Best": world_class_best,
                    "Gap to Industry": f"{gap_industry:.2f}",
                    "Status vs. Industry": status_industry,
                    "Gap to World-Class": f"{gap_world_class:.2f}",
                    "Status vs. World-Class": status_world_class
                })
                bar_chart_data.append({
                    "Metric": metric,
                    "Your Value": user_value,
                    "Industry Best": industry_best,
                    "World-Class Best": world_class_best
                })
        
        if bar_chart_data:
            df_plot = pd.DataFrame(bar_chart_data)
            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=df_plot['Metric'],
                y=df_plot['Your Value'],
                name='Your Value',
                marker_color='indianred'
            ))
            fig.add_trace(go.Bar(
                x=df_plot['Metric'],
                y=df_plot['Industry Best'],
                name='Industry Best',
                marker_color='lightsalmon'
            ))
            fig.add_trace(go.Bar(
                x=df_plot['Metric'],
                y=df_plot['World-Class Best'],
                name='World-Class Best',
                marker_color='darkblue'
            ))

            fig.update_layout(
                barmode='group',
                title_text='Your Performance vs. Benchmarks',
                xaxis_title="Metric",
                yaxis_title="Value",
                title_x=0.5
            )
            plot_data = fig.to_json()


    return render_template("benchmarking.html", comparison_results=comparison_results_list, plot_data=plot_data)

# --- Routine Dynamics Explorer Logic (From Day 4 Project) ---
@app.route("/routines", methods=["GET", "POST"])
def routines_page():
    routine_results = []
    routine_advice = []

    if request.method == "POST":
        delegate_routine = request.form.get("delegate_routine", "").strip()
        documented_routine = request.form.get("documented_routine", "").strip()

        if delegate_routine and documented_routine:
            delegate_steps = [s.strip() for s in delegate_routine.split(',') if s.strip()]
            documented_steps = [s.strip() for s in documented_routine.split(',') if s.strip()]

            # 1. Compare Step Presence
            for doc_step in documented_steps:
                if doc_step not in delegate_steps:
                    routine_results.append({"Step": doc_step, "Source": "Documented", "Status": "Omitted by Delegate"})
                else:
                    routine_results.append({"Step": doc_step, "Source": "Documented", "Status": "Followed"})
            
            for del_step in delegate_steps:
                if del_step not in documented_steps:
                    routine_results.append({"Step": del_step, "Source": "Delegate", "Status": "Added by Delegate"})

            # 2. Compare Step Order (simplified check)
            order_mismatch = False
            if len(delegate_steps) == len(documented_steps):
                if delegate_steps != documented_steps:
                    order_mismatch = True
            else: # If lengths are different, order is implicitly mismatched for common steps
                common_steps_doc_order = [s for s in documented_steps if s in delegate_steps]
                common_steps_del_order = [s for s in delegate_steps if s in documented_steps]
                if common_steps_doc_order != common_steps_del_order:
                    order_mismatch = True


            # Generate Advice based on findings
            omitted_steps = [r['Step'] for r in routine_results if r['Status'] == 'Omitted by Delegate']
            added_steps = [r['Step'] for r in routine_results if r['Status'] == 'Added by Delegate']
            followed_steps_count = len([r for r in routine_results if r['Status'] == 'Followed'])
            total_documented_steps = len(documented_steps)
            
            if not omitted_steps and not added_steps and not order_mismatch:
                routine_advice.append("Excellent adherence! The delegate's routine matches the documented procedure perfectly. This indicates strong process control and training effectiveness. This is a characteristic of **High Reliability Organizations (HROs)** demonstrating **Commitment to Resilience** by standardizing best practices, **Preoccupation with Failure** by ensuring no steps are missed, and **Reluctance to Simplify** by following the complete, detailed routine.")
            else:
                if omitted_steps:
                    routine_advice.append(f"**Omitted Steps Detected:** The delegate omitted the following steps: {', '.join(omitted_steps)}. This is a significant concern as omissions can lead to system failures, especially in complex operations. It highlights a potential lack of **Preoccupation with Failure** and a **Reluctance to Simplify** complex realities. Investigate why these steps were missed.")
                if added_steps:
                    routine_advice.append(f"**Added Steps Detected:** The delegate added the following steps: {', '.join(added_steps)}. While some additions might be positive adaptations, unauthorized additions can introduce variability and unforeseen risks. This suggests a deviation from the documented process, which can sometimes be a sign of 'workarounds' or 'drift'. Analyze these additions to understand if they are beneficial 'work-arounds' (positive drift) that should be incorporated, or unsafe 'work-arounds' (negative drift) that need correction. This relates to **Sensitivity to Operations** – understanding what is actually happening.")
                if order_mismatch:
                    routine_advice.append("**Step Reordering Detected:** The sequence of steps differed from the documented procedure. Order is often critical in complex routines. This signifies a form of routine drift. Analyze if the reordering was a necessary adaptation or a source of potential error. This is crucial for **Deference to Expertise** – ensuring the best method is followed regardless of hierarchy, and counteracting the **Normalization of Deviation**.")
                
                if (followed_steps_count / total_documented_steps) < 0.8 and not omitted_steps and not added_steps and not order_mismatch: # edge case for very few followed steps if logic above wasn't perfect
                    routine_advice.append("Significant deviations from the documented routine were observed. This indicates potential gaps in training, procedure clarity, or a 'normalization of deviation.'")
                elif not routine_advice: # Fallback for minor, hard-to-categorize drifts
                     routine_advice.append("Subtle deviations or inconsistencies in the routine were identified. Even small variations can accumulate and lead to significant risks over time (e.g., 'Normalization of Deviation'). Foster a culture of **Chronic Unease** to identify and address these minor drifts before they become major issues.")

    return render_template("routines.html", routine_results=routine_results, routine_advice=routine_advice)

# --- Risk Strategy Navigator Logic (New Module) ---
# Define scores for likelihood and impact
LIKELIHOOD_SCORES = {
    "Rare": 1,
    "Unlikely": 2,
    "Possible": 3,
    "Likely": 4,
    "Almost Certain": 5
}

IMPACT_SCORES = {
    "Insignificant": 1,
    "Minor": 2,
    "Moderate": 3,
    "Major": 4,
    "Catastrophic": 5
}

def calculate_risk_score(likelihood, impact):
    try:
        return LIKELIHOOD_SCORES[likelihood] * IMPACT_SCORES[impact]
    except KeyError:
        return 0 # Handle cases where input might not match predefined levels

def classify_risk(score):
    if score >= 16: # Example threshold for High
        return "High"
    elif score >= 9: # Example threshold for Medium
        return "Medium"
    else:
        return "Low"

def get_risk_category_and_advice(likelihood_level, impact_level):
    likelihood_score = LIKELIHOOD_SCORES.get(likelihood_level, 0)
    impact_score = IMPACT_SCORES.get(impact_level, 0)
    
    risk_advice = ""
    category = "Other Risks" # Default category

    if likelihood_score >= 4 and impact_score >= 4: # High Severity, High Frequency (HSHF)
        category = "High Severity, High Frequency (HSHF) Risks"
        risk_advice = "HSHF: These are urgent, high-priority risks. They demand **Immediate, Radical Intervention**, focusing on **Root Cause Elimination** and fundamental **Process Redesign**. Strategies include applying **TRIZ principles** like 'Segmentation' or 'Prior Action' to break down the problem or prevent it entirely. Reconsider fundamental assumptions and eliminate the conditions that allow the risk to manifest frequently with high impact. These often reflect a 'Fixes That Fail' or 'Shifting the Burden' archetype if not addressed systemically."
    elif likelihood_score <= 2 and impact_score >= 4: # High Severity, Low Frequency (HSLF)
        category = "High Severity, Low Frequency (HSLF) Risks"
        risk_advice = "HSLF: These are 'Black Swan' type risks that can be catastrophic but are rare. Focus on **Robust Design**, **Redundancy** (e.g., multiple layers of defense), and fostering a culture of **Chronic Unease**. Implement **Resilience Planning** and **Contingency Reserves**. The goal is not prevention of the event itself (as it's rare) but minimization of its impact and ensuring rapid recovery. This aligns with a 'Limits to Growth' or 'Tragedy of the Commons' archetype if the system is allowed to deplete its own resilience."
    elif likelihood_score >= 4 and impact_score <= 2: # Low Severity, High Frequency (LSHF)
        category = "Low Severity, High Frequency (LSHF) Risks"
        risk_advice = "LSHF: These are nuisance risks that can erode morale and efficiency over time. Focus on **Process Optimization** and **Standardization**. Implement quick, iterative improvements. While individually minor, their cumulative effect can be significant (similar to 'Accumulation'). Automate where possible to reduce human error. Don't let these become 'Normalized Deviations'."
    else:
        risk_advice = "General risk management advice: For 'Other Risks' (Medium/Low Priority), prioritize based on score and available resources. Implement standard controls, monitor regularly, and review periodically."
    
    return category, risk_advice


@app.route("/risk_navigator", methods=["GET", "POST"])
def risk_navigator_page():
    if 'risks_data' not in session:
        session['risks_data'] = []

    if request.method == "POST":
        if 'risk_name' in request.form:
            risk_name = request.form['risk_name']
            likelihood = request.form['likelihood']
            impact = request.form['impact']

            if risk_name.strip() and likelihood and impact:
                score = calculate_risk_score(likelihood, impact)
                priority = classify_risk(score)
                category, advice = get_risk_category_and_advice(likelihood, impact)

                session['risks_data'].append({
                    "Risk Name": risk_name,
                    "Likelihood": likelihood,
                    "Impact": impact,
                    "Score": score,
                    "Priority": priority,
                    "Category": category,
                    "Advice": advice
                })
        elif 'clear_all_risks' in request.form:
            session['risks_data'] = []
            return redirect(url_for('risk_navigator_page'))

    # Prepare data for Plotly heatmap
    risk_matrix_data = [[0 for _ in range(5)] for _ in range(5)]
    x_labels = list(IMPACT_SCORES.keys())
    y_labels = list(LIKELIHOOD_SCORES.keys())

    # Map scores to colors for the heatmap background
    colorscale_values = [
        [0, 'rgb(144, 238, 144)'],    # Light Green (Low)
        [0.5, 'rgb(255, 255, 0)'],    # Yellow (Medium)
        [0.8, 'rgb(255, 165, 0)'],    # Orange (Medium-High)
        [1, 'rgb(255, 0, 0)']       # Red (High)
    ]

    # Create the heatmap background
    z_values = [
        [1, 2, 3, 4, 5],
        [2, 4, 6, 8, 10],
        [3, 6, 9, 12, 15],
        [4, 8, 12, 16, 20],
        [5, 10, 15, 20, 25]
    ]

    heatmap_trace = go.Heatmap(
        z=z_values,
        x=x_labels,
        y=y_labels,
        colorscale='Viridis', # You can choose a different colorscale here if 'Viridis' isn't what you want
        showscale=True,
        hovertemplate="Likelihood: %{y}<br>Impact: %{x}<br>Score: %{z}<extra></extra>"
    )

    # Add submitted risks as scatter points on top of the heatmap
    risk_points = []
    if session['risks_data']:
        for risk in session['risks_data']:
            risk_points.append(go.Scatter(
                x=[risk['Impact']],
                y=[risk['Likelihood']],
                mode='markers',
                marker=dict(symbol='circle', size=15, color='black',
                            line=dict(width=2, color='white')),
                name=f"Risk: {risk['Risk Name']}",
                hoverinfo='text',
                hovertext=f"<b>Risk:</b> {risk['Risk Name']}<br>"
                            f"<b>Likelihood:</b> {risk['Likelihood']}<br>"
                            f"<b>Impact:</b> {risk['Impact']}<br>"
                            f"<b>Score:</b> {risk['Score']}<br>"
                            f"<b>Priority:</b> {risk['Priority']}<br>"
                            f"<b>Category:</b> {risk['Category']}<br>"
                            f"<b>Advice:</b> {risk['Advice']}",
                showlegend=False
            ))

    risk_fig = go.Figure(data=[heatmap_trace] + risk_points)

    risk_fig.update_layout(
        title_text='Risk Assessment Matrix',
        xaxis_title='Impact',
        yaxis_title='Likelihood',
        xaxis_type='category',
        yaxis_type='category',
        xaxis_tickangle=-45,
        title_x=0.5
    )

    plot_data = risk_fig.to_json()

    # Categorize risks for display
    hshf_risks = [r for r in session['risks_data'] if r['Category'] == "High Severity, High Frequency (HSHF) Risks"]
    hslf_risks = [r for r in session['risks_data'] if r['Category'] == "High Severity, Low Frequency (HSLF) Risks"]
    other_risks = [r for r in session['risks_data'] if r['Category'] == "Other Risks" or r['Category'] == "Low Severity, High Frequency (LSHF) Risks"]
    
    # Get distinct advice for each category, as multiple risks might have the same advice
    hshf_advice = list(set([r['Advice'] for r in hshf_risks]))
    hslf_advice = list(set([r['Advice'] for r in hslf_risks]))
    other_advice = list(set([r['Advice'] for r in other_risks]))


    return render_template("risk_navigator.html", 
                           risks=session['risks_data'], 
                           plot_data=plot_data,
                           hshf_risks=hshf_risks,
                           hslf_risks=hslf_risks,
                           other_risks=other_risks,
                           hshf_advice=hshf_advice,
                           hslf_advice=hslf_advice,
                           other_advice=other_advice)

if __name__ == "__main__":
    app.run(debug=True)