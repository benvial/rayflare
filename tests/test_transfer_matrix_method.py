from pytest import approx
import numpy as np

def test_tmm_structure():
    from rayflare.transfer_matrix_method import tmm_structure


    tmm_setup = tmm_structure([])
    RAT = tmm_setup.calculate(wavelength=np.array([]))


    assert sorted(list(RAT.keys())) == ["A", "A_per_layer", "R", "T", "all_p", "all_s"]


def test_inc_coh_tmm():
    from solcore import material, si
    from solcore.structure import Layer
    from solcore.solar_cell import SolarCell
    from rayflare.transfer_matrix_method import tmm_structure

    GaInP = material("GaInP")(In=0.5)
    GaAs = material("GaAs")()
    Ge = material("Ge")()

    optical_struct = SolarCell(
        [
            Layer(material=GaInP, width=si("5000nm")),
            Layer(material=GaAs, width=si("200nm")),
            Layer(material=GaAs, width=si("5um")),
            Layer(material=Ge, width=si("50um")),
        ]
    )

    wl = np.linspace(400, 1200, 5)

    c_list = [
        ["c", "c", "c", "c"],
        ["c", "c", "c", "i"],
        ["c", "i", "i", "c"],
        ["i", "i", "i", "i"],
    ]


    results = []
    for cl in c_list:
        tmm_setup = tmm_structure(optical_struct, coherent=False, coherency_list=cl, no_back_reflection=False)
        RAT = tmm_setup.calculate(wl, angle=0, pol='u')
        results.append(np.sum(RAT['A_per_layer'], 1))

    A_calc = np.stack(results)
    A_data = np.array(
        [
            [0.5742503, 0.67956899, 0.73481184, 0.725372, 0.76792856],
            [0.5742503, 0.67956899, 0.73481184, 0.725372, 0.76792856],
            [0.5742503, 0.67956899, 0.73474943, 0.70493469, 0.70361194],
            [0.5742503, 0.67956899, 0.70927724, 0.71509221, 0.71592772]
        ]
    )
    assert A_calc == approx(A_data)


def test_sp_pol():
    from solcore import material, si
    from solcore.structure import Layer
    from solcore.solar_cell import SolarCell
    from rayflare.transfer_matrix_method import tmm_structure

    GaInP = material("GaInP")(In=0.5)
    GaAs = material("GaAs")()
    Ge = material("Ge")()

    optical_struct = SolarCell(
        [
            Layer(material=GaInP, width=si("5000nm")),
            Layer(material=GaAs, width=si("200nm")),
            Layer(material=GaAs, width=si("6um")),
            Layer(material=Ge, width=si("5um")),
        ]
    )

    wl = np.linspace(400, 1200, 10)

    results_s = []

    for angle in [0, np.pi/4, np.pi/3, 0.49*np.pi]:
        tmm_setup = tmm_structure(optical_struct, coherent=True, no_back_reflection=False)
        RAT = tmm_setup.calculate(wl, angle=angle, pol='s')
        results_s.append(np.sum(RAT['A_per_layer'], 1))

    A_calc_s = np.stack(results_s)

    results_p = []

    for angle in [0, np.pi/4, np.pi/3, 0.49*np.pi]:
        tmm_setup = tmm_structure(optical_struct, coherent=True, no_back_reflection=False)
        RAT = tmm_setup.calculate(wl, angle=angle, pol='p')
        results_p.append(np.sum(RAT['A_per_layer'], 1))

    A_calc_p = np.stack(results_p)

    results_u = []

    for angle in [0, np.pi/4, np.pi/3, 0.49*np.pi]:
        tmm_setup = tmm_structure(optical_struct, coherent=True, no_back_reflection=False)
        RAT = tmm_setup.calculate(wl, angle=angle, pol='u')
        results_u.append(np.sum(RAT['A_per_layer'], 1))

    A_calc_u = np.stack(results_u)

    assert A_calc_u == approx(0.5*(A_calc_s + A_calc_p))

    A_data = np.array([
        [0.5742503 , 0.65157195, 0.67832579, 0.68226493, 0.68535974,
        0.67909547, 0.65763539, 0.66792418, 0.75304704, 0.74521762],
       [0.45434853, 0.52749112, 0.5539266 , 0.55795924, 0.55894821,
        0.55075466, 0.54622101, 0.63196572, 0.52299822, 0.51144073],
       [0.34887414, 0.41235227, 0.43601998, 0.43963046, 0.47651039,
        0.50886181, 0.49166823, 0.57972568, 0.48556919, 0.42998698],
       [0.02663692, 0.0329389 , 0.03545789, 0.03586407, 0.03615642,
        0.03558688, 0.04200677, 0.04284779, 0.05441022, 0.05403772]
    ])

    assert A_calc_s == approx(A_data)


def test_tmm_structure_abs():
    from solcore import si, material
    from solcore.structure import Layer
    from rayflare.transfer_matrix_method import tmm_structure
    from solcore.solar_cell import SolarCell

    InGaP = material('GaInP')(In=0.5)
    GaAs = material('GaAs')()
    Ge = material('Ge')()
    Ag = material('Ag')()

    Al2O3 = material('Al2O3')()

    # anti-reflection coating

    wavelengths = np.linspace(250, 1900, 200) * 1e-9

    RCWA_wl = wavelengths

    options = {'pol': 's',
               'wavelengths': RCWA_wl,
               'parallel': True,
               'n_jobs': -1,
               'theta_in': 0,
               'phi_in': 0,
               'A_per_order': False}

    ARC = [Layer(si('80nm'), Al2O3)]

    solar_cell = SolarCell(ARC + [Layer(material=InGaP, width=si('400nm')),
                                  Layer(material=GaAs, width=si('4000nm')),
                                  Layer(material=Ge, width=si('3000nm'))], substrate=Ag)

    tmm_setup = tmm_structure(solar_cell, coherent=True)

    integrated = np.zeros((6, 3))
    j1 = 0
    for pol in ['s', 'p', 'u']:
        for angle in [0, 60]:
            options['pol'] = pol
            options['theta_in'] = angle

            tmm_result = tmm_setup.calculate(wavelength=wavelengths * 1e9, pol=pol, angle=angle * np.pi / 180)

            integr = 1e4*np.trapz(
                wavelengths[:, None] * 1e9 * tmm_result['A_per_layer'],
                wavelengths * 1e9, axis=0) / 1e9

            integrated[j1, :] = integr[1:]

            j1 += 1

    expected = np.array([[1.4234972 , 1.67748004, 7.35621745],
       [1.35543244, 1.30592315, 5.28228305],
       [1.4234972 , 1.67748004, 7.35621745],
       [1.44652436, 1.65923102, 8.43831573],
       [1.4234972 , 1.67748004, 7.35621745],
       [1.4009784 , 1.48257709, 6.86029939]])
    assert approx(integrated == expected)
