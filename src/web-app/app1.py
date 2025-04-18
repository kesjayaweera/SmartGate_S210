from flask import Flask, render_template
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

@app.route('/')
def stats():
    # 1. Create Table Data
    df_species = pd.DataFrame({
        'Species': ['Bear', 'Fox', 'Dog', 'Cat', 'Crab', 'Boar', 'Bat'],
        'Detections': [6, 4, 8, 7, 3, 5, 4]
    })
    
    # 2. Gate Activity Data
    df_time = pd.DataFrame({
        'Time': ['0:00', '4:00', '8:00', '12:00', '16:00', '20:00', '24:00'],
        'Gate Opened': [5, 10, 15, 12, 8, 6, 2],
        'Gate Closed': [3, 6, 12, 14, 7, 4, 1]
    })

    # 3. Save bar chart
    plt.figure()
    df_species.plot(x='Species', y='Detections', kind='bar', legend=False, color='skyblue')
    plt.title("Most Frequently Detected Species")
    plt.ylabel("No. of times detected")
    plt.tight_layout()
    plt.savefig('static/bar_chart.png')
    plt.close()

    # 4. Save line chart
    plt.figure()
    df_time.plot(x='Time', y=['Gate Opened', 'Gate Closed'], kind='line', marker='o')
    plt.title("Gate Activity Over Time")
    plt.ylabel("No. of times")
    plt.tight_layout()
    plt.savefig('static/line_chart.png')
    plt.close()

    # Convert table to HTML
    table_html = df_species.to_html(classes='table table-striped', index=False, border=0)

    return render_template('stats.html', table=table_html)

if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True)
