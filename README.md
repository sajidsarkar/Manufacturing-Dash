# Manufacturing Quality Analytics Dashboard

The goal of this project was to create an interactive analytics dashboard that can be used to easily analyze manufacturing quality defects and prioritize and impelement manufacturing corrective action projects based on the analysis. It was more important share this dashboard to manufacturing stakeholders by giving easy access to everyone.

Below is a brief description of how it was achieved.
 - Manufacturing data was collected using API and pythong requests library

 - Data was processed using python pandas libarary
 - Data visualizations were created using Plotly
 - The dashboard was created using Dash
 - The dashboard was finally deployed using Heroku
 - Here is the link to the website.

**Main Achievement:** The manufacturing team was missing a medium where it can view all critical production metrics agglomerated in a one spot. The lack of such a medium discouraged stakeholders to make data driven decisions. Therefore, deployment of this dashboard was an effective solution to that problem.

**Future Work:** This is just the tip of an iceberg. My intention is to continue modifying this dashboard based on the feedback I receive from manufacturing team. Also, I intend to add more metrics, categorize them into different group, and add a sidebar for navigating the metric groups. A challenge will be to optimize data capture from API and computation with growing number of contents or metrics, as too much computation (especially transfer of data) will slow down the web application.
