# Eksperimentalna evaluacija: uticaj procesnog konteksta na kvalitet detekcije

## Cilj i postavka eksperimenta

Cilj ovog eksperimenta je provera glavne tvrdnje rada: da povezivanje mrežnih
događaja sa stanjem procesa poboljšava kvalitet detekcije u odnosu na pristup
zasnovan isključivo na mrežnim pravilima. Poboljšanje se ovde meri kroz dva
efekta — tačniju ocenu ozbiljnosti (podizanje alarma koji imaju stvarnu
procesnu posledicu) i smanjenje broja lažnih ili preglasnih alarma (spuštanje
događaja koji nemaju procesni kontekst).

Da bi poređenje bilo pošteno, oba pristupa se izvršavaju nad **istim ulazom** i
kroz **istu putanju obrade**. Ulaz je jedan snimljeni saobraćaj (`pair.pcap`)
zajedno sa istovremeno snimljenom procesnom telemetrijom (`pair_telemetry.jsonl`),
pri čemu su mreža i proces beleženi na istoj vremenskoj osi. Snimak sadrži
normalan saobraćaj (periodično očitavanje registara od strane HMI i SCADA
klijenata) i šest neovlašćenih Modbus upisa koje generiše napadač (`rogue-sim`,
adresa 192.168.10.99). Tokom snimanja legitimni HMI klijent ne izdaje komande
pumpama, čime se obezbeđuje da je jedini izvor upisa napadač i da svaki
detektovani neovlašćeni upis potiče iz poznatog, kontrolisanog izvora.

Razlika između dva pristupa svedena je na jednu konfiguracionu zastavicu
(`CORRELATION_ENABLED`). Kada je isključena, korelacioni korak se izvršava, ali
ne menja ozbiljnost alarma (prolaz bez izmene). Kada je uključena, korelacija za
svaki alarm ispituje procesnu telemetriju u vremenskom prozoru [T − 5 s, T + 5 s]
oko trenutka događaja i na osnovu utvrđene procesne promene podiže ili spušta
ozbiljnost. Time je obezbeđeno da se meri isti sistem u obe konfiguracije, a ne
dva različita sistema — jedina promenljiva je prisustvo procesnog konteksta.

Merenje se sprovodi tako što se isti snimak pušta kroz sistem dva puta: jednom
sa isključenom i jednom sa uključenom korelacijom. Nakon svakog prolaza broji se
količina alarma po nivou ozbiljnosti. Pošto se determinisani ulaz obrađuje
determinisanom logikom, ponovljena merenja daju identičan rezultat, što
poređenje čini ponovljivim po konstrukciji.

## Rezultati

Tabela prikazuje broj alarma po nivou ozbiljnosti, bez i sa uključenom
korelacijom, nad istim snimkom.

| Ozbiljnost | Bez korelacije | Sa korelacijom |
|------------|:--------------:|:--------------:|
| CRITICAL   |        0       |        1       |
| HIGH       |        7       |        6       |
| MEDIUM     |        1       |        0       |
| INFO       |        0       |        1       |
| **Ukupno** |      **8**     |      **8**     |

Ukupan broj alarma je u obe konfiguracije jednak (8). Korelacija, dakle, ne
uvodi nove alarme niti ih uklanja — ona preraspoređuje postojeće alarme po
nivou ozbiljnosti na osnovu procesnog konteksta.

## Tumačenje

Rezultat pokazuje tri pomeranja, od kojih svako potvrđuje po jedan aspekt
glavne tvrdnje.

**Podizanje ozbiljnosti (0 → 1 CRITICAL).** Napadač je izveo šest neovlašćenih
Modbus upisa, koje pravilo RULE-007 u oba slučaja prepoznaje kao neovlašćeni
upis i inicijalno ocenjuje nivoom HIGH. Sa uključenom korelacijom, jedan od tih
upisa je podignut na nivo CRITICAL, jer se u njegovom vremenskom prozoru desila
stvarna promena stanja pumpe. Drugim rečima, taj upis nije bio samo mrežno
neovlašćen, već je i fizički pomerio proces. Ovu razliku pristup zasnovan samo
na mrežnim pravilima ne može da vidi, jer on nema uvid u stanje procesa.
Preostalih pet upisa zadržalo je nivo HIGH, pošto se nisu poklopili sa procesnom
promenom (napadač ne poznaje trenutno stanje postrojenja, pa deo njegovih upisa
 upisuje vrednost koju pumpa već ima i time ne izaziva promenu). Sposobnost
sistema da razlikuje upis koji je pomerio proces od upisa koji nije upravo je
ono što procesni kontekst dodaje.

**Spuštanje ozbiljnosti (1 MEDIUM → 1 INFO).** Pojava napadača na mreži okida
pravilo RULE-001 (pojavio se nov uređaj), inicijalno ocenjeno nivoom MEDIUM. Sa
uključenom korelacijom, taj događaj je spušten na nivo INFO, jer sama pojava
uređaja u posmatranom prozoru nema procesnu posledicu. Ovo odgovara realnom
rasuđivanju: pojava novog uređaja na mreži jeste podatak vredan beleženja, ali
sama po sebi nije napad — za razliku od upisa koji menja stanje postrojenja.
Spuštanjem takvih događaja na informativni nivo smanjuje se broj alarma koji bi
operatera nepotrebno opterećivali, što je direktna potvrda dela tvrdnje koji se
odnosi na smanjenje lažnih i preglasnih alarma.

**Nepromenjen ukupan broj (8 → 8).** Činjenica da se ukupan broj alarma ne menja
potvrđuje da korelacija ne radi tako što potiskuje ili izmišlja događaje, već
tako što isti skup događaja preciznije rangira. To je važno za pouzdanost
sistema: nijedan događaj nije izgubljen, samo je tačnije ocenjen.

## Ograničenja

Rezultati su dobijeni nad jednim, namenski pripremljenim scenarijem, pa ih treba
tumačiti kao demonstraciju mehanizma, a ne kao statistički reprezentativnu meru
nad raznovrsnim saobraćajem. Broj podignutih alarma zavisi od toga koliko se
napadačevih upisa vremenski poklopi sa stvarnom promenom procesa; u ovom snimku
to je bio jedan upis. Bogatiji skup scenarija (više napada, različiti obrasci
upisa, promenljivo opterećenje) dao bi raspodelu iz koje bi se mogli izvesti
kvantitativni pokazatelji, što je prirodan pravac za proširenje evaluacije.

Takođe, determinisanost merenja — ista prednost koja obezbeđuje ponovljivost —
znači da rezultat odražava ponašanje sistema nad ovim konkretnim ulazom.
Uopštavanje na proizvoljan saobraćaj zahtevalo bi ponavljanje eksperimenta nad
većim brojem nezavisnih snimaka. Konačno, širina korelacionog prozora (5 s)
predstavlja kompromis: preuzak prozor može propustiti procesnu promenu koja
kasni za mrežnim događajem, dok preširok prozor može povezati događaje koji
nemaju stvarnu uzročnu vezu. U ovom radu prozor je izabran znatno širim od
intervala osvežavanja procesa (100 ms na strani simulatora), čime je rizik od
promašaja usled sporog osvežavanja sveden na najmanju meru; sistematsko
ispitivanje uticaja širine prozora ostavljeno je za dalji razvoj.
