from app import app, StockRequest
import json

def check_requests():
    with app.app_context():
        requests = StockRequest.query.all()
        result = []
        for r in requests:
            result.append({
                "id": r.id,
                "request_id": r.request_id,
                "item_name": r.item_name,
                "status": r.status,
                "total_kits": r.total_kits
            })
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    check_requests()
