class SimulationParameter:
    def __init__(self, Nx, Ny, Nz, Lx, Ly, Lz, Cy, Ax, Vx, Ay, Vy, Az, Vz, Wli, Wsh, Wsa, Cr, Fr, rendiment, Nli, Nsh,
                 Nsa, bay_level,
                 tech, strat, strat_par_x, strat_par_y, adjacency=None):
        self.rendiment = rendiment
        self.Fr = Fr
        self.Cr = Cr
        if tech == 0 or tech == 1:
            self.Nsa = 1
        else:
            self.Nsa = Nsa
        if tech == 0:
            self.Nsh = 1
        else:
            self.Nsh = Nsh
        self.Nli = Nli
        self.Vz = Vz
        self.Az = Az
        self.Vy = Vy
        self.Ay = Ay
        self.Vx = Vx
        self.Ax = Ax
        self.Cy = Cy
        self.Wli = Wli
        self.Wsh = Wsh
        self.Wsa = Wsa
        self.Lz = Lz
        self.Ly = Ly
        self.Lx = Lx
        self.Nz = Nz
        self.Ny = Ny
        self.Nx = Nx
        self.bay_level = bay_level
        self.tech = tech
        self.strategy = strat
        self.strategy_par_x = strat_par_x
        self.strategy_par_y = strat_par_y
        self.adjacency = adjacency