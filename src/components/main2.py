from fastapi import FastAPI, Request, Response, BackgroundTasks
from fastapi.templating import Jinja2Templates
import threading
from producer import fetch_stock_price, toggle_producer, historical_data
from consumer import consume_stock_prices, toggle_consumer, kafka_data_queue
import logging
import plotly.express as px
from starlette.responses import HTMLResponse

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize Kafka data list
kafka_data = []
kafka_data_event = threading.Event()

def fetch_data_from_queue():
    global kafka_data

    while True:
        data = kafka_data_queue.get()
        kafka_data.append(data)
        kafka_data_event.set()  # Signal that new data is available

# Start a thread to fetch data from the queue
data_fetch_thread = threading.Thread(target=fetch_data_from_queue)
data_fetch_thread.start()

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def index(request: Request):
    global kafka_data, historical_data

    # Create historical chart
    if historical_data:
        historical_data_chart = {
            'Symbol': [item['symbol'] for item in historical_data],
            'Price': [item['price'] for item in historical_data],
        }
        historical_fig = px.line(historical_data_chart, x='Symbol', y='Price', title='Historical Stock Prices')
        historical_chart_div = historical_fig.to_html(full_html=False)
    else:
        historical_chart_div = "<p>No historical data available.</p>"

    return templates.TemplateResponse('index.html', {"request": request, "historical_chart": historical_chart_div})

@app.post("/")
async def index_post(request: Request):
    form_data = await request.form()
    if 'start' in form_data:
        toggle_producer(True)  # Start data production
        toggle_consumer(True)  # Start data consumption
    elif 'stop' in form_data:
        toggle_producer(False)  # Stop data production
        toggle_consumer(False)  # Stop data consumption

    return Response(status_code=303, headers={"Location": "/"})

@app.get("/real-time")
async def real_time():
    global kafka_data, kafka_data_event

    # Wait for the event to be set, but with a timeout to avoid blocking indefinitely
    if not kafka_data_event.wait(timeout=30):
        # No new data within the timeout
        real_time_chart_div = "<p>No real-time data available.</p>"

    # Clear the event flag for the next iteration
    kafka_data_event.clear()

    # Create a Plotly bar chart using the fetched real-time data
    if kafka_data:
        real_time_data = {
            'Symbol': [item['symbol'] for item in kafka_data],
            'Price': [item['price'] for item in kafka_data],
        }

        # Create a Plotly bar chart for real-time data
        real_time_fig = px.bar(real_time_data, x='Symbol', y='Price', title='Real-Time Stock Prices')

        # Convert the real-time chart to HTML
        real_time_chart_div = real_time_fig.to_html(full_html=False)
    else:
        real_time_chart_div = "<p>No real-time data available.</p>"

    return HTMLResponse(content=real_time_chart_div)

if __name__ == "__main__":
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA','NVDA']
    threads = []

    for symbol in symbols:
        try:
            t = threading.Thread(target=fetch_stock_price, args=(symbol,), name=symbol)
            t.start()
            threads.append(t)
            logger.info(f'Started thread for {symbol}')
        except Exception as e:
            logger.error(f'Error starting thread for {symbol}: {e}')

    consumer_thread = threading.Thread(target=consume_stock_prices)
    consumer_thread.start()

    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8080)
