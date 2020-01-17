#include <vector>
#include <iostream>
#include "Pythia8Plugins/HepMC2.h"

void CorrectWeights(HepMC::WeightContainer & in) {
	int verb = 0;
	if (verb > 0) std::cout << "-- Have " << in.size() << " weights\n";
	std::cout.precision(9);
	std::vector<double> out(in.size(), 0.);
	// unsigned N = (in.size() - 2) / 2;
	int N = (-3 + int(sqrt(9.0 + 8.0 * (double(in.size()) - 2.0)) + 0.5)) / 2;
	for (unsigned i = 0; i < in.size(); ++i) {
		if (verb > 0) std::cout << " - " << in[i] << "\n";
		out[i] = in[i];
	}
	for (unsigned ip = 0; ip < N; ++ip) {
		double s0 = in[1];
		double s1 = in[ip * 2 + 2];
		double s2 = in[ip * 2 + 3];
		if (verb > 0) std::cout << " -- Doing " << ip << "\n";
		if (verb > 0) std::cout << s0 << "\t" << s1 << "\t" << s2 << "\n";
		s1 -= s0;
		s2 -= s0;
		if (verb > 0) std::cout << " - subtract s0: " << s1 << "\t" << s2 << "\n";
		double Ai = 4. * s1 - s2;
		double Bii = s2 - Ai;
		if (verb > 0) std::cout << " - Result: " << Ai << "\t" << Bii << "\n";
		out[ip * 2 + 2] = Ai;
		out[ip * 2 + 3] = Bii;
	}
	unsigned crossed_offset = 2 + 2 * N;
	unsigned c_counter = 0;
	for (unsigned ix = 0; ix < N; ++ix) {
		for (unsigned iy = ix + 1; iy < N; ++iy) {
			if (verb > 0) std::cout << " -- Doing " << ix << "\t" << iy << "\t[" << (crossed_offset + c_counter) << "]\n";
			double s = in[crossed_offset + c_counter];
			double sm = in[1];
			double sx = out[ix * 2 + 2];
			double sy = out[iy * 2 + 2];
			double sxx = out[ix * 2 + 3];
			double syy = out[iy * 2 + 3];
			s -= (sm + sx + sy + sxx + syy);
			out[crossed_offset + c_counter] = s;
			if (verb > 0) std::cout << " - Result: " << s << "\n";
			++c_counter;
		}
	}
	for (unsigned i = 0; i < in.size(); ++i) {
		in[i] = out[i];
	}
	// return out;
}