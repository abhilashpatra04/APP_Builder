from flask import Flask, request, jsonify

app = Flask(__name__)

class CalculatorServer:
    def add(self, num1, num2):
        return num1 + num2

    def subtract(self, num1, num2):
        return num1 - num2

    def multiply(self, num1, num2):
        return num1 * num2

    def divide(self, num1, num2):
        if num2 == 0:
            return 'Error: Division by zero'
        return num1 / num2

server = CalculatorServer()

@app.route('/add', methods=['POST'])
def handle_add):
    data = request.get_json()
    num1 = data['num1']
    num2 = data['num2']
    result = server.add(num1, num2)
    return jsonify({'result': result})

@app.route('/subtract', methods=['POST'])
def handle_subtract):
    data = request.get_json()
    num1 = data['num1']
    num2 = data['num2']
    result = server.subtract(num1, num2)
    return jsonify({'result': result})

@app.route('/multiply', methods=['POST'])
def handle_multiply):
    data = request.get_json()
    num1 = data['num1']
    num2 = data['num2']
    result = server.multiply(num1, num2)
    return jsonify({'result': result})

@app.route('/divide', methods=['POST'])
def handle_divide):
    data = request.get_json()
    num1 = data['num1']
    num2 = data['num2']
    result = server.divide(num1, num2)
    return jsonify({'result': result})

if __name__ == '__main__':
    app.run(debug=True)