import math

from Resources.Movement import Position, distance
from SimMain.SimulationParameter import SimulationParameter


def energy(pos1, pos2, par, weight) -> float:
    assert isinstance(pos1, Position)
    assert isinstance(pos2, Position)
    assert isinstance(par, SimulationParameter)
    ret = 0
    g = 9.81
    d = distance(pos1, pos2, par)
    #lift
    if pos1.level != pos2.level:
        d_lim = (par.Ay * math.pow(par.Vy / par.Ay, 2))
        if d_lim * 2 < d:
            t_const = (d - 2 * d_lim) / par.Vy
            t_acc = par.Vy / par.Ay
            t_tot = t_acc + t_const
            v_term = par.Vy
        else:
            t_tot = math.sqrt(d / par.Ay)
            t_acc = t_tot / 2
            v_term = (t_tot / 2) * par.Ay
            t_const = 0
        # giong up or down
        if pos2.level > pos1.level:
            pow_acc = (par.Ay * par.Fr + g + g * par.Cr) * (v_term / par.rendiment)
            pow_decc = (-par.Ay * par.Fr + g + g * par.Cr) * (v_term / par.rendiment)
            pow_decc = pow_decc if pow_decc > 0 else 0
            pow_const = (g + g * par.Cr) * par.Vy / par.rendiment
        else:
            pow_acc = (-par.Ay * par.Fr + g - g * par.Cr) * (v_term / par.rendiment)
            pow_decc = (par.Ay * par.Fr + g - g * par.Cr) * (v_term / par.rendiment)
            pow_decc = pow_decc if pow_decc > 0 else 0
            pow_const = (g - g * par.Cr) * par.Vy / par.rendiment
        if d_lim * 2 < d:
            ret = pow_acc * t_acc + pow_decc * t_acc + pow_const * t_const
        else:
            ret = pow_acc * t_acc / 2 + pow_decc * t_acc / 2
    # shuttle
    elif pos1.x != pos2.x:
        d_lim = (par.Ax * math.pow(par.Vx / par.Ax, 2)) / 2
        if d_lim * 2 < d:
            t_const = (d - 2 * d_lim) / par.Vx
            t_acc = par.Vx / par.Ax
            t_tot = t_acc * 2 + t_const
            v_term = par.Vx
        else:
            t_tot = math.sqrt(d / par.Ax)
            t_acc = t_tot / 2
            v_term = (t_tot / 2) * par.Ax
            t_const = 0
        pow_acc = (par.Ax * par.Fr + g * par.Cr) * (v_term / par.rendiment)
        pow_decc = (par.Ax * par.Fr - g * par.Cr) * (v_term / par.rendiment)
        pow_decc = pow_decc if pow_decc > 0 else 0
        # todo pay attention at low v
        pow_const = g * par.Cr * par.Vx / par.rendiment
        if d_lim * 2 < d:
            ret = pow_acc * t_acc + pow_decc * t_acc + pow_const * t_const
        else:
            ret = pow_acc * t_acc / 2 + pow_decc * t_acc / 2
    #satellite
    elif pos1.z != pos2.z:
        d_lim = (par.Az * math.pow(par.Vz / par.Az, 2))
        if d_lim * 2 < d:
            t_const = (d - 2 * d_lim) / par.Vz
            t_acc = par.Vz / par.Az
            t_tot = t_acc + t_const
            v_term = par.Vz
        else:
            t_tot = math.sqrt(d / par.Az)
            t_acc = t_tot / 2
            v_term = (t_tot / 2) * par.Az
            t_const = 0
        pow_acc = (par.Az * par.Fr + g * par.Cr) * (v_term / par.rendiment)
        pow_decc = (par.Az * par.Fr - g * par.Cr) * (v_term / par.rendiment)
        pow_decc = pow_decc if pow_decc > 0 else 0

        # todo pay attention at low v
        pow_const = g * par.Cr * par.Vz / par.rendiment
        if d_lim * 2 < d:
            ret = pow_acc * t_acc + pow_decc * t_acc + pow_const * t_const
        else:
            ret = pow_acc * t_acc / 2 + pow_decc * t_acc / 2
    else:
        return 0

    return ret * weight * 0.000277778
