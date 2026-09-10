"""
plant2.py — MOZAK DRUGOG PLC-a (regulacija pritiska)

Drugi PLC u postrojenju: reguliše pritisak u cevi pomoću ventila.
Simetričan prvom PLC-u (pumpe/nivo), ali sa drugom fizikom (ventil/pritisak).

Logika: kada je ventil ZATVOREN, pritisak raste (nešto ga gura, a nema kud).
Kada je ventil OTVOREN, pritisak pada (ispušta se). Ako pritisak pređe
gornju granicu -> kvar (opasno visok pritisak). Ovo daje realan scenario
napada: neko zatvori ventil i digne pritisak do opasnog nivoa.
"""

from dataclasses import dataclass
import time


@dataclass
class StanjePritiska:
    ventil_otvoren: bool = True      # ventil: otvoren = ispušta, zatvoren = drži
    pritisak: float = 30.0           # pritisak u barima (0-100), kreće umereno
    kvar: bool = False
    razlog_kvara: str = ""


class Pritisak:
    """Mozak drugog PLC-a. Drži StanjePritiska i otkucava ga metodom korak()."""

    PORAST_PO_SEK = 8.0          # kad je ventil zatvoren, pritisak raste
    PAD_PO_SEK = 10.0            # kad je ventil otvoren, pritisak pada
    DOTOK_PO_SEK = 2.0           # stalni dotok koji gura pritisak nagore
    CILJNI_PRITISAK = 30.0       # normalan radni pritisak

    PRAG_OPASNO = 90.0           # iznad ovoga je kvar (previsok pritisak)
    PRAG_NIZAK = 5.0             # ispod ovoga je kvar (pao pritisak)

    def __init__(self):
        self.stanje = StanjePritiska()
        self._poslednje_vreme = time.monotonic()

    # ---------- Komande (zvace ih Modbus/OPC UA) ----------

    def otvori_ventil(self):
        self.stanje.ventil_otvoren = True

    def zatvori_ventil(self):
        self.stanje.ventil_otvoren = False

    # ---------- Glavni takt ----------

    def korak(self, dt: float | None = None):
        if dt is None:
            sada = time.monotonic()
            dt = sada - self._poslednje_vreme
            self._poslednje_vreme = sada

        s = self.stanje

        # Stalni dotok gura pritisak nagore
        promena = self.DOTOK_PO_SEK * dt

        if s.ventil_otvoren:
            # Ventil otvoren -> ispušta -> pritisak pada
            promena -= self.PAD_PO_SEK * dt
            # Blaga regulacija ka cilju kad je ventil otvoren (normalan rad)
            greska = self.CILJNI_PRITISAK - s.pritisak
            promena += 0.5 * greska * dt
        else:
            # Ventil zatvoren -> pritisak raste
            promena += self.PORAST_PO_SEK * dt

        s.pritisak += promena
        s.pritisak = max(0.0, min(100.0, s.pritisak))

        # Provera kvara
        if s.pritisak >= self.PRAG_OPASNO:
            s.kvar = True
            s.razlog_kvara = "Previsok pritisak"
        elif s.pritisak <= self.PRAG_NIZAK:
            s.kvar = True
            s.razlog_kvara = "Prenizak pritisak"
        else:
            s.kvar = False
            s.razlog_kvara = ""

    def prikazi(self) -> str:
        s = self.stanje
        ventil = "OTVOREN" if s.ventil_otvoren else "ZATVOREN"
        kvar = f"  KVAR: {s.razlog_kvara}" if s.kvar else ""
        return (f"Pritisak: {s.pritisak:5.1f} bar  |  "
                f"Ventil: {ventil}{kvar}")

    # ---------- Interfejs ProcessDevice (opis za genericke servere) ----------

    def step(self, dt: float | None = None) -> None:
        """Alias za korak() — ime iz interfejsa ProcessDevice."""
        self.korak(dt)

    def render(self) -> str:
        """Alias za prikazi() — ime iz interfejsa ProcessDevice."""
        return self.prikazi()

    def coil_outputs(self) -> list[int]:
        s = self.stanje
        # redosled adresa: 0=ventil_otvoren, 1=kvar
        return [int(s.ventil_otvoren), int(s.kvar)]

    def register_outputs(self) -> list[int]:
        s = self.stanje
        # redosled adresa: 0=pritisak*10
        return [int(s.pritisak * 10)]

    def apply_coils(self, coils: list[int]) -> None:
        # coil[0] -> ventil (1=otvori, 0=zatvori)
        v = coils[0] if len(coils) > 0 else 0

        if v and not self.stanje.ventil_otvoren:
            self.otvori_ventil()
        elif not v and self.stanje.ventil_otvoren:
            self.zatvori_ventil()

    def opcua_structure(self) -> dict:
        # imena cvorova za drugi PLC — Edge ce se kasnije pretplatiti na njih
        return {
            "Ventil": [("Otvoren", True)],
            "Cev": [("Pritisak", 0.0), ("Kvar", False)],
        }

    def opcua_values(self) -> dict:
        s = self.stanje
        return {
            "Ventil": {"Otvoren": s.ventil_otvoren},
            "Cev": {"Pritisak": float(s.pritisak), "Kvar": s.kvar},
        }


if __name__ == "__main__":
    p = Pritisak()
    print("== Start: pritisak 30 bar, ventil otvoren ==")
    print(p.prikazi())

    print("\n== Zatvaram ventil. Pritisak treba da raste ka opasnom. ==")
    p.zatvori_ventil()
    for i in range(12):
        p.korak(dt=1.0)
        print(f"t={i+1:2d}s  {p.prikazi()}")

    print("\n== Otvaram ventil. Pritisak treba da padne ka normali. ==")
    p.otvori_ventil()
    for i in range(10):
        p.korak(dt=1.0)
        print(f"t={i+13:2d}s  {p.prikazi()}")