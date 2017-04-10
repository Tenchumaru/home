#pragma once

// https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm
template<typename T, typename FN>
void Bresenham0(T x0, T y0, T x1, T y1, FN fn) {
	auto dx = x1 - x0;
	auto dy = y1 - y0;
	auto D = dx - 2 * dy;
	while(x0 < x1) {
		fn(x0, y0);
		if(D < 0) {
			++y0;
			D += 2 * dx;
		}
		D -= 2 * dy;
		++x0;
	}
}

template<typename T, typename D, typename FN>
void Bresenham2(T x0, T y0, T x1, D dx, D dy, FN fn) {
	auto d = dx - 2 * dy;
	while(x0 < x1) {
		fn(x0, y0);
		if(d < 0) {
			++y0;
			d += 2 * dx;
		}
		d -= 2 * dy;
		++x0;
	}
}

template<typename T, typename FN>
void Bresenham1(T x0, T y0, T x1, T y1, FN fn) {
	auto dx = x1 - x0;
	auto dy = y1 - y0;
	if(dx < dy) {
		Bresenham2(y0, x0, y1, dy, dx, [fn](T x, T y) { fn(y, x); });
	} else {
		Bresenham2(x0, y0, x1, dx, dy, fn);
	}
}

template<typename T, typename FN>
void Bresenham(T x0, T y0, T x1, T y1, FN fn) {
	if(x1 < x0) {
		if(y1 < y0) {
			Bresenham1(-x0, -y0, -x1, -y1, [fn](T x, T y) { fn(-x, -y); });
		} else {
			Bresenham1(-x0, y0, -x1, y1, [fn](T x, T y) { fn(-x, y); });
		}
	} else {
		if(y1 < y0) {
			Bresenham1(x0, -y0, x1, -y1, [fn](T x, T y) { fn(x, -y); });
		} else {
			Bresenham1(x0, y0, x1, y1, fn);
		}
	}
}
