# solar-tilt

Computes the fixed tilt angle for a south-facing solar panel that maximizes annual insolation at a given latitude. Clear-sky geometric model, standard library only.

```bash
python solar_tilt.py --lat 40.08 --plot
```

## The model

Three equations, all from Duffie & Beckman, *Solar Engineering of Thermal Processes*:

- Cooper's equation for solar declination as a function of day-of-year
- Extraterrestrial daily radiation on a horizontal surface (eq. 1.10.3)
- `Rb`, the beam radiation tilt factor (eq. 2.19.1)

Integrate `H0 * Rb` over 365 days, sweep tilt from 0 to 70 degrees, take the max.

## Known problem: this model is biased high

Run it at latitude 40 and it says the optimal tilt is ~38.5 degrees, i.e. roughly equal to the latitude. That is the textbook clear-sky answer and it is **not what you should actually build.**

Real installations at 40°N do better around 30-33 degrees. The reason is that the model only accounts for *beam* radiation — direct sunlight. It ignores the diffuse component scattered by the atmosphere, which arrives from the whole sky dome rather than from the sun's position. Diffuse radiation is captured better by a flatter panel, so including it pulls the optimum down. In cloudy climates diffuse can be 40-60% of total insolation, which is a lot to be leaving out.

The `rule of thumb` line in the output prints the Landau approximation (`0.76 * lat + 3.1`), which is fit to empirical data and does account for diffuse. The gap between the two numbers is the size of the error.

**So: the number this program prints is an upper bound on the correct tilt, not the correct tilt.** Fixing it means adding an isotropic diffuse model (Liu & Jordan) plus a clearness index for the site, which requires actual weather data. That's the next version.

## The finding that does hold up

Look at the `--plot` output. Anything between about 30 and 48 degrees lands within 1% of optimal. The curve is extremely flat near the peak.

This matters practically: if your roof pitch is anywhere in that range, matching it costs you almost nothing versus a tilted rack. The optimization is real but the stakes are low, which is the kind of thing an optimizer will never tell you if you only print the argmax.

## TODO

- [ ] Liu & Jordan isotropic diffuse model
- [ ] Pull clearness index from NREL NSRDB by lat/lon
- [ ] Azimuth as a free parameter (currently hardcoded due south)
- [ ] Southern hemisphere
- [ ] Compare against PVWatts for a few sites as a sanity check
