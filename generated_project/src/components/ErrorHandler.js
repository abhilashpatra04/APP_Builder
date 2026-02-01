import React, { Component } from 'react';

class ErrorHandler extends Component {
  constructor(props) {
    super(props);
    this.state = {
      errorMessage: ''
    };
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.error) {
      this.setState({ errorMessage: nextProps.error.message });
    }
  }

  render() {
    return (
      <div>
        {this.state.errorMessage ? (
          <div style={{ color: 'red' }}>
            <h2>Error</h2>
            <p>{this.state.errorMessage}</p>
          </div>
        ) : null}
      </div>
    );
  }
}

export default ErrorHandler;
