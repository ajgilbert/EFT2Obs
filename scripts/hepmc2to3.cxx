// Convert HepMC2 ASCII format to HepMC3 ASCII format
// Usage: hepmc2to3 input.hepmc [output.hepmc]  (stdout if no output given)
#include "HepMC3/ReaderAsciiHepMC2.h"
#include "HepMC3/WriterAscii.h"
#include "HepMC3/GenEvent.h"
#include <memory>
#include <string>
#include <iostream>

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: hepmc2to3 <input.hepmc> [output.hepmc]\n";
        return 1;
    }
    std::string infile = argv[1];
    std::string outfile = (argc >= 3) ? argv[2] : "-";

    HepMC3::ReaderAsciiHepMC2 reader(infile);
    if (reader.failed()) {
        std::cerr << "ERROR: cannot open input file: " << infile << "\n";
        return 1;
    }

    std::shared_ptr<HepMC3::WriterAscii> writer;
    if (outfile == "-") {
        writer = std::make_shared<HepMC3::WriterAscii>(std::cout);
    } else {
        writer = std::make_shared<HepMC3::WriterAscii>(outfile);
    }

    int nevt = 0;
    while (!reader.failed()) {
        HepMC3::GenEvent evt;
        reader.read_event(evt);
        if (reader.failed()) break;
        writer->write_event(evt);
        ++nevt;
        if (nevt % 1000 == 0)
            std::cerr << "Converted " << nevt << " events\r";
    }
    writer->close();
    reader.close();
    std::cerr << "\nDone: converted " << nevt << " events.\n";
    return 0;
}
