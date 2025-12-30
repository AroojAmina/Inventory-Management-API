from bottle import Bottle, run, request, response
import json

# App instance
app = Bottle()

# Fake database (list of todos)
todos = [
    {"id": 1, "task": "Learn Bottle", "done": False},
    {"id": 2, "task": "Practice Python", "done": True}
]

# Helper function for JSON response
def json_response(data, status=200):
    response.content_type = "application/json"
    response.status = status
    return json.dumps(data)


# Routes


@app.get("/")
def home():
    return json_response({"message": "Welcome to Bottle Todo API"})


@app.get("/todos")
def get_todos():
    """List all todos"""
    return json_response(todos)


@app.get("/todos/<todo_id:int>")
def get_todo(todo_id):
    """Get a single todo by ID"""
    todo = next((t for t in todos if t["id"] == todo_id), None)
    if todo:
        return json_response(todo)
    return json_response({"error": "Todo not found"}, 404)


@app.post("/todos")
def create_todo():
    """Create a new todo"""
    data = request.json
    if not data or "task" not in data:
        return json_response({"error": "Task is required"}, 400)

    new_todo = {
        "id": len(todos) + 1,
        "task": data["task"],
        "done": False
    }
    todos.append(new_todo)
    return json_response(new_todo, 201)


@app.put("/todos/<todo_id:int>")
def update_todo(todo_id):
    """Update a todo"""
    data = request.json
    todo = next((t for t in todos if t["id"] == todo_id), None)

    if not todo:
        return json_response({"error": "Todo not found"}, 404)

    todo["task"] = data.get("task", todo["task"])
    todo["done"] = data.get("done", todo["done"])
    return json_response(todo)


@app.delete("/todos/<todo_id:int>")
def delete_todo(todo_id):
    """Delete a todo"""
    global todos
    todos = [t for t in todos if t["id"] != todo_id]
    return json_response({"message": "Todo deleted"})


# Run app
if __name__ == "__main__":
    run(app, host="localhost", port=8080, debug=True)
