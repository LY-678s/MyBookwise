import traceback
from django.db import DatabaseError

def main():
    try:
        from bookstore.models import Orders
        order_id = 3
        print("Testing OrderID:", order_id)
        try:
            updated = Orders.objects.filter(pk=order_id).update(status=2)
            print("bulk update result, updated =", updated)
        except DatabaseError as e:
            print("bulk update raised DatabaseError:", e)
            code = e.args[0] if getattr(e, "args", None) else None
            print("error code:", code)
            if code == 1442:
                print("Detected MySQL 1442, falling back to per-order save()")
                try:
                    o = Orders.objects.get(pk=order_id)
                    o.status = 2
                    o.save()
                    print("per-order save succeeded for OrderID", order_id)
                except Exception as ex:
                    print("per-order save failed:", ex)
                    traceback.print_exc()
            else:
                traceback.print_exc()
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    main()


