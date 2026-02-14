# Quick Commerce Admin Dashboard

This is a premium, responsive dashboard for managing the Quick Commerce backend.

## Features

- **Overview**: Real-time summary of orders, products, and issues.
- **Product Management**: Browse and inspect the product catalog.
- **Inventory Tracking**: Monitor stock levels across different store hubs.
- **Order Management**: Track customer orders and their processing status.
- **DLQ Inspection**: Manage failed orders and attempt retries.
- **Store Load Monitoring**: Visualize current load, latency, and velocity per store.

## How to Run

1. **Start the Backend**:
   Make sure the FastAPI backend is running on `http://localhost:8000`.

   ```bash
   uvicorn app.main:app --reload
   ```

2. **Run the Dashboard**:
   Since it uses standard web technologies, you can serve it using any web server. The simplest way is using Python:
   ```bash
   cd admin-dashboard
   python -m http.server 8001
   ```
   Then open `http://localhost:8001` in your browser.

## Technologies Used

- **HTML5 & CSS3**: Custom premium styling with Glassmorphism.
- **Vanilla JavaScript**: Modular logic for high performance and zero dependencies.
- **Lucide Icons**: Modern, consistent iconography.
- **Inter Font**: Clean, professional typography.
- **FastAPI Integration**: Seamless communication with the core backend services.
