# Eksperimentalna evaluacija: brzina obrade i potrošnja resursa

## Cilj i postavka eksperimenta

Cilj ovog eksperimenta je provera druge tvrdnje rada: da lanac obrade
`paketi → tokovi → događaji → alarmi` dovoljno smanjuje količinu podataka da
uređaj obradu obavi na vreme i bez prevelike potrošnje resursa. Uz to se meri i
koliko procesni kontekst (korelacija) košta u pogledu brzine, čime se odgovara
na drugi deo istraživačkog pitanja.

Merenje se sprovodi nad istim snimljenim saobraćajem (`pair.pcap`) koji je
korišćen i u evaluaciji kvaliteta detekcije. Edge aplikacija se pokreće u
režimu ponovnog puštanja snimka: učita snimljene pakete, obradi ih kroz ceo
lanac (izgradnja tokova, primena pravila, korelacija, upis u bazu) i završi.
Mereni su sledeći pokazatelji: vreme obrade mrežnog dela, propusnost izražena
brojem obrađenih paketa u sekundi, vršna rezidentna memorija procesa i ukupno
utrošeno procesorsko vreme. Vršna memorija i procesorsko vreme očitavaju se
unutar samog procesa (`resource.getrusage`), što za kratkotrajan proces daje
pouzdaniju vrednost od spoljašnjeg uzorkovanja.

Svako merenje ponovljeno je tri puta, a prikazane vrednosti su prosek. Pošto se
determinisani ulaz obrađuje determinisanom logikom, odstupanje između prolaza je
malo (ispod 2% kod vremena obrade), što potvrđuje ponovljivost merenja.

## Rezultati: lanac smanjenja količine

Osnovni princip na kome sistem počiva jeste da se ne čuva svaki paket, već
sažetak saobraćaja u obliku tokova. Nad posmatranim snimkom lanac smanjenja
izgleda ovako:

| Nivo    | Količina |
|---------|:--------:|
| Paketi  |   4879   |
| Tokovi  |     6    |
| Upisi   |     6    |

Broj tokova čini svega 0,12% broja paketa. Drugim rečima, umesto skoro pet
hiljada pojedinačnih paketa, sistem u bazi pamti šest zapisa toka, uz šest
detektovanih neovlašćenih upisa koji se izdvajaju za dodatnu analizu. Ovako
izražen odnos posledica je prirode industrijskog saobraćaja: komunikacija se
odvija između malog broja stalnih uređaja preko malog broja trajnih konekcija,
pa se veliki broj paketa svodi na mali broj tokova. Upravo ta pravilnost čini
sažimanje u tokove delotvornim — što je saobraćaj repetitivniji, to je ušteda
veća.

## Rezultati: brzina i potrošnja

| Pokazatelj              | Vrednost        |
|-------------------------|-----------------|
| Prosečno vreme obrade   | 1,72 s          |
| Propusnost              | ~2840 paketa/s  |
| Vršna memorija          | ~157 MB         |
| Procesorsko vreme       | 4,58 s          |

Propusnost od približno 2840 paketa u sekundi dovoljna je za brzine saobraćaja
koje se javljaju u laboratorijskom okruženju (reda nekoliko megabita u sekundi).
Vršna memorija od oko 157 MB je skromna i uklapa se u ograničenja slabijeg
hardvera, što je bitno za planirani prelazak na ugrađene platforme. Procesorsko
vreme veće je od stvarnog vremena obrade jer se deo posla (sinhrono čitanje
snimka i obrada) izvršava u zasebnoj niti, pa se koristi više od jednog jezgra.

## Rezultati: cena procesnog konteksta

Da bi se utvrdilo koliko korelacija košta, isti snimak je obrađen u dve
konfiguracije — sa uključenom i isključenom korelacijom.

| Konfiguracija      | Vreme obrade | Propusnost      |
|--------------------|:------------:|:---------------:|
| Bez korelacije     |    1,47 s    | ~3326 paketa/s  |
| Sa korelacijom     |    1,72 s    | ~2840 paketa/s  |

Uključivanje korelacije produžava obradu za približno 0,25 s, odnosno oko 17%,
dok potrošnja memorije ostaje praktično nepromenjena (~157 MB). Ovaj trošak
proizlazi iz toga što korelacija za svaki alarm izvršava jedan upit nad
procesnom telemetrijom u posmatranom vremenskom prozoru. Zbog toga cena
korelacije raste sa brojem alarma, a ne sa brojem paketa: na saobraćaju sa malo
alarma dodatni trošak je zanemarljiv, dok bi na velikom broju alarma rastao
linearno.

Ovaj rezultat zajedno sa evaluacijom kvaliteta detekcije daje potpun odgovor na
istraživačko pitanje: procesni kontekst poboljšava detekciju (tačnija ozbiljnost
i manje lažnih alarma) uz umeren trošak od oko 17% u brzini obrade i bez dodatne
potrošnje memorije. Ovakav kompromis opravdava uvođenje procesnog konteksta u
posmatranom okruženju.

## Ograničenja

Merenje je izvedeno u režimu ponovnog puštanja snimka, u kome Edge učitava i
obrađuje snimljene pakete iz datoteke. Ovaj režim je pogodan za ponovljivo
merenje propusnosti i potrošnje, ali ne obuhvata ponašanje sistema pri obradi
saobraćaja u realnom vremenu, gde bi pri dovoljno velikom prilivu moglo doći do
odbacivanja paketa. Utvrđivanje tačke zasićenja — opterećenja pri kome sistem
prestaje da stiže sa obradom — zahteva izvor saobraćaja koji se generiše uživo i
sniffing u realnom vremenu, što u korišćenom Docker okruženju na Windows
platformi nije podržano na način koji bi dao pouzdanu meru. Iz tog razloga je
ispitivanje tačke zasićenja, zajedno sa merenjem na ugrađenom hardveru
(Raspberry Pi) i eventualnim prelaskom na brže mehanizme obrade (AF_PACKET,
Zeek ili implementacija u jeziku C), ostavljeno za dalji razvoj.

Takođe, prikazani odnos smanjenja količine (paketi naspram tokova) zavisi od
sastava saobraćaja u snimku. Na raznovrsnijem saobraćaju sa većim brojem
različitih konekcija broj tokova bio bi veći, pa bi odnos bio blaži nego u ovom
merenju. Prikazane vrednosti stoga treba tumačiti kao ilustraciju principa
sažimanja, a ne kao univerzalni odnos.
