import React, { Component } from 'react';
import { jsPDF } from 'jspdf';

class PDFMerger extends Component {
  constructor(props) {
    super(props);
    this.state = {
      pdfFiles: [],
      mergedPDF: null
    };
  }

  mergePDFs = () => {
    const { pdfFiles } = this.props;
    const pdf = new jsPDF();

    pdfFiles.forEach((pdfFile) => {
      const pdfContent = pdfFile.content;
      const pdfPages = pdfContent.split('\\n');

      pdfPages.forEach((page) => {
        pdf.text(page, 10, 10);
        pdf.addPage();
      });
    });

    this.setState({ mergedPDF: pdf.output('blob') });
  };

  render() {
    return (
      <div>
        <button onClick={this.mergePDFs}>Merge PDFs</button>
        {this.state.mergedPDF && (
          <a href={URL.createObjectURL(this.state.mergedPDF)} download="merged.pdf">Download Merged PDF</a>
        )}
      </div>
    );
  }
}

export default PDFMerger;
