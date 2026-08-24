"""
plant.py — MOZAK SIMULATORA POSTROJENJA

Ovaj fajl drži stanje jednog malog postrojenja i menja ga kroz vreme.
NAMERNO ne zna ništa o mreži (Modbus, OPC UA) — to su odvojeni fajlovi.
Njegov jedini posao: pamtiti stanje procesa i ažurirati ga na svaki "takt".

Model je namerno jednostavan. Cilj NIJE realan hidraulički proračun,
nego da postoji jasna, dosledna veza između akcije (pumpa) i posledice (nivo),
da bi kasnije povezivanje mrežnih i procesnih događaja imalo šta da uhvati.
"""

from dataclasses import dataclass, field
import time


@dataclass
class StanjePostrojenja:
    """
    Sve promenljive stanja postrojenja na jednom mestu.
    dataclass = Python način da napraviš 'kutiju za podatke' bez pisanja
    gomile koda. Svako polje ima podrazumevanu vrednost (pocetno stanje).
    """
    # --- Pumpa 1 (puni rezervoar) ---
    pumpa1_radi: bool = False        # da li pumpa radi
    pumpa1_brzina: float = 0.0       # brzina u Hz (0 kad ne radi)

    # --- Pumpa 2 (prazni rezervoar) ---
    pumpa2_radi: bool = False
    pumpa2_brzina: float = 0.0

    # --- Rezervoar ---
    nivo: float = 50.0               # nivo u procentima (0-100), krece na pola

    # --- Alarmi / kvar ---
    kvar: bool = False               # opsti indikator kvara
    razlog_kvara: str = ""           # tekstualni opis zasto je kvar


class Postrojenje:
    """
    Postrojenje = mozak. Drzi StanjePostrojenja i ume da ga 'otkuca' napred
    u vremenu metodom korak().

    Konstante (KAP_*, PRAG_*) su na vrhu da se lako menjaju bez diranja logike.
    """

    # Punjenje i praznjenje su priblizno jednaki, tako da kad obe pumpe rade
    # (normalan rad) nivo lebdi oko sredine umesto da bezi ka dnu ili vrhu.
    # Blaga regulacija (v. korak()) dodatno vraca nivo ka cilju.
    PUNJENJE_PO_SEK = 5.0            # pumpa1 dodaje do 5% u sekundi
    PRAZNJENJE_PO_SEK = 5.0         # pumpa2 oduzima do 5% u sekundi
    CURENJE_PO_SEK = 0.05           # rezervoar lagano curi i sam

    # Ciljni nivo za regulaciju u normalnom radu
    CILJNI_NIVO = 50.0

    # Granice za kvar
    PRAG_PREPUN = 95.0
    PRAG_PRAZAN = 5.0

    # Nominalna brzina pumpe kad radi (Hz)
    NOMINALNA_BRZINA = 50.0

    def __init__(self):
        self.stanje = StanjePostrojenja()
        self._poslednje_vreme = time.monotonic()

    # ---------- Komande (kasnije ce ih zvati Modbus/OPC UA) ----------

    def upali_pumpu1(self):
        self.stanje.pumpa1_radi = True
        self.stanje.pumpa1_brzina = self.NOMINALNA_BRZINA

    def ugasi_pumpu1(self):
        self.stanje.pumpa1_radi = False
        self.stanje.pumpa1_brzina = 0.0

    def upali_pumpu2(self):
        self.stanje.pumpa2_radi = True
        self.stanje.pumpa2_brzina = self.NOMINALNA_BRZINA

    def ugasi_pumpu2(self):
        self.stanje.pumpa2_radi = False
        self.stanje.pumpa2_brzina = 0.0

    # ---------- Glavni takt ----------

    def korak(self, dt: float | None = None):
        """
        Otkucaj postrojenje napred za dt sekundi.
        Ako dt nije zadat, sam racuna koliko je proslo od proslog poziva
        (realno vreme). Zadavanje dt rucno je korisno za testove.
        """
        if dt is None:
            sada = time.monotonic()
            dt = sada - self._poslednje_vreme
            self._poslednje_vreme = sada

        s = self.stanje

        # 1) Promena nivoa na osnovu pumpi
        promena = 0.0
        if s.pumpa1_radi:
            promena += self.PUNJENJE_PO_SEK * dt
        if s.pumpa2_radi:
            promena -= self.PRAZNJENJE_PO_SEK * dt
        promena -= self.CURENJE_PO_SEK * dt   # stalno malo curi

        # 1b) Blaga regulacija: kad obe pumpe rade (normalan rad), pumpa1
        # malo pojaca/popusti da vrati nivo ka cilju. Ovo simulira realnu
        # regulaciju i drzi "normalu" mirnom oko CILJNI_NIVO.
        if s.pumpa1_radi and s.pumpa2_radi:
            greska = self.CILJNI_NIVO - s.nivo      # koliko smo ispod/iznad cilja
            promena += 0.5 * greska * dt            # blago koriguj-vrati ka cilju

        s.nivo += promena

        # 2) Nivo ne moze van 0-100
        s.nivo = max(0.0, min(100.0, s.nivo))

        # 3) Provera kvara
        if s.nivo >= self.PRAG_PREPUN:
            s.kvar = True
            s.razlog_kvara = "Rezervoar prepun"
        elif s.nivo <= self.PRAG_PRAZAN:
            s.kvar = True
            s.razlog_kvara = "Rezervoar prazan"
        else:
            s.kvar = False
            s.razlog_kvara = ""

    def prikazi(self) -> str:
        """Kratak tekstualni prikaz stanja, za proveru u terminalu."""
        s = self.stanje
        p1 = "RADI" if s.pumpa1_radi else "stoji"
        p2 = "RADI" if s.pumpa2_radi else "stoji"
        kvar = f"  KVAR: {s.razlog_kvara}" if s.kvar else ""
        return (f"Nivo: {s.nivo:5.1f}%  |  "
                f"Pumpa1: {p1} ({s.pumpa1_brzina:.0f}Hz)  |  "
                f"Pumpa2: {p2} ({s.pumpa2_brzina:.0f}Hz){kvar}")


# ---------- Provera: pokreni ovaj fajl direktno da vidis da mozak radi ----------
if __name__ == "__main__":
    """
    Ako pokrenes 'python3 plant.py', ovaj deo simulira scenario:
    upali pumpu1, gledaj kako nivo raste, pa upali pumpu2, gledaj kako se stabilizuje.
    Ovo je test mozga BEZ mreze — dokaz da se stanje ponasa logicno.
    """
    p = Postrojenje()

    print("== Start: nivo 50%, obe pumpe stoje ==")
    print(p.prikazi())

    print("\n== Palim samo Pumpu1 (punjenje). Nivo treba da raste. ==")
    p.upali_pumpu1()
    for i in range(8):
        p.korak(dt=1.0)          # simuliraj 1 sekundu po koraku
        print(f"t={i+1:2d}s  {p.prikazi()}")

    print("\n== Palim i Pumpu2. Praznjenje jace od punjenja -> nivo se smiruje. ==")
    p.upali_pumpu2()
    for i in range(8):
        p.korak(dt=1.0)
        print(f"t={i+9:2d}s  {p.prikazi()}")

    print("\n== Gasim Pumpu1, ostaje samo Pumpa2. Nivo treba da pada ka kvaru. ==")
    p.ugasi_pumpu1()
    for i in range(8):
        p.korak(dt=1.0)
        print(f"t={i+17:2d}s  {p.prikazi()}")