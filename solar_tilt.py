#!/usr/bin/env python3
"""
solar-tilt: find the fixed panel tilt that maximizes annual insolation
at a given latitude.

Uses a clear-sky geometric model. No weather, no clouds, no shading.
Standard library only.

Usage:
    python solar_tilt.py --lat 40.08
    python solar_tilt.py --lat 40.08 --plot
"""

import argparse
import math

RAD = math.pi / 180


def declination(day_of_year):
    """Solar declination in degrees. Cooper's equation (1969)."""
    return 23.45 * math.sin(RAD * 360 * (284 + day_of_year) / 365)


def hour_angle_sunset(lat, decl):
    """Sunset hour angle in degrees, for a horizontal surface."""
    x = -math.tan(lat * RAD) * math.tan(decl * RAD)
    # Clamp for polar day/night
    x = max(-1.0, min(1.0, x))
    return math.acos(x) / RAD


def extraterrestrial_daily(lat, day):
    """
    Daily extraterrestrial radiation on a horizontal surface, MJ/m^2.
    Duffie & Beckman eq. 1.10.3.
    """
    gsc = 0.0820  # solar constant, MJ/m^2/min
    decl = declination(day)
    ws = hour_angle_sunset(lat, decl)
    eccentricity = 1 + 0.033 * math.cos(RAD * 360 * day / 365)

    return (24 * 60 / math.pi) * gsc * eccentricity * (
        math.cos(lat * RAD) * math.cos(decl * RAD) * math.sin(ws * RAD)
        + (ws * RAD) * math.sin(lat * RAD) * math.sin(decl * RAD)
    )


def tilt_factor(lat, tilt, day):
    """
    Ratio of beam radiation on a south-facing tilted surface to that on a
    horizontal surface (Rb). Duffie & Beckman eq. 2.19.1.

    Northern hemisphere, panel facing due south, azimuth = 0.
    """
    decl = declination(day)
    effective_lat = lat - tilt

    ws = hour_angle_sunset(lat, decl)
    # Sunset angle on the tilted surface can be earlier than on horizontal
    ws_tilt = min(ws, hour_angle_sunset(effective_lat, decl))

    num = (
        math.cos(effective_lat * RAD) * math.cos(decl * RAD) * math.sin(ws_tilt * RAD)
        + (ws_tilt * RAD) * math.sin(effective_lat * RAD) * math.sin(decl * RAD)
    )
    den = (
        math.cos(lat * RAD) * math.cos(decl * RAD) * math.sin(ws * RAD)
        + (ws * RAD) * math.sin(lat * RAD) * math.sin(decl * RAD)
    )
    if den <= 0:
        return 0.0
    return max(0.0, num / den)


def annual_insolation(lat, tilt):
    """Sum of daily tilted insolation over the year, MJ/m^2."""
    total = 0.0
    for day in range(1, 366):
        h0 = extraterrestrial_daily(lat, day)
        if h0 <= 0:
            continue
        total += h0 * tilt_factor(lat, tilt, day)
    return total


def optimize(lat, lo=0, hi=70, step=0.5):
    """Brute-force search. The function is smooth and unimodal, so this is fine."""
    best_tilt, best_val = lo, -1.0
    t = lo
    while t <= hi:
        v = annual_insolation(lat, t)
        if v > best_val:
            best_tilt, best_val = t, v
        t += step
    return best_tilt, best_val


def ascii_plot(lat, best):
    print("\n  tilt   annual insolation (relative)")
    baseline = annual_insolation(lat, best)
    for t in range(0, 71, 5):
        v = annual_insolation(lat, t) / baseline
        bar = "#" * int(v * 50)
        marker = "  <-- optimal" if abs(t - best) < 2.5 else ""
        print(f"  {t:>3}deg  {bar} {v:.3f}{marker}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lat", type=float, required=True, help="latitude, degrees north")
    p.add_argument("--plot", action="store_true", help="print an ascii sensitivity plot")
    args = p.parse_args()

    if not -66 < args.lat < 66:
        print("This model assumes mid-latitudes and a south-facing panel.")
        print("Results outside +/-66 degrees are not meaningful.")
        return

    if args.lat < 0:
        print("Southern hemisphere not supported. Flip the sign and face north.")
        return

    tilt, val = optimize(args.lat)
    flat = annual_insolation(args.lat, 0)

    print(f"latitude:       {args.lat:.2f} deg N")
    print(f"optimal tilt:   {tilt:.1f} deg")
    print(f"rule of thumb:  {args.lat * 0.76 + 3.1:.1f} deg  (Landau approximation)")
    print(f"gain vs flat:   {100 * (val / flat - 1):+.1f}%")

    if args.plot:
        ascii_plot(args.lat, tilt)


if __name__ == "__main__":
    main()
