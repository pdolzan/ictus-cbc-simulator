
import math
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# --- PATHS ---
ROOT = Path(__file__).parent
DATA = ROOT / "data"
ICON = ROOT / "images" / "icon.png"
IMAGES = ROOT / "images"

# --- ICTUS BRAND ---
NAVY = "#003A6E"
YELLOW = "#FAC108"
LIGHT_BLUE = "#EEF5FA"
LIGHT_YELLOW = "#FFF8DF"
LIGHT_GREY = "#F6F8FA"
MID_GREY = "#D9E1E8"
TEXT = "#17324D"
WHITE = "#FFFFFF"

st.set_page_config(
    page_title="Simulator zaposlitvenega paketa",
    page_icon=str(ICON) if ICON.exists() else "📊",
    layout="wide",
)

st.markdown(f"""
<style>
.stApp {{ background-color:{WHITE}; color:{TEXT}; }}
.block-container {{ max-width:1180px; padding-top:2rem; padding-bottom:3rem; }}
h1,h2,h3 {{ color:{NAVY}; }}
div[data-testid="stMetric"] {{
 background:{LIGHT_GREY}; border:1px solid {MID_GREY}; border-radius:12px; padding:16px;
}}
/* TAB TEXT - vedno NAVY */
.stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"] {{
    color:{NAVY} !important;
}}

.stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"] p {{
    color:{NAVY} !important;
}}

/* AKTIVEN TAB - tekst ostane NAVY */
.stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] {{
    color:{NAVY} !important;
}}

.stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] p {{
    color:{NAVY} !important;
}}

/* NEAKTIVEN TAB - tekst prav tako NAVY */
.stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="false"] {{
    color:{NAVY} !important;
}}

.stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="false"] p {{
    color:{NAVY} !important;
}}

/* Rdeča črta pod aktivnim tabom */
.stTabs [data-baseweb="tab-highlight"] {{
    background-color:red !important;
}}
.attr-label {{
 min-height:38px; display:flex; align-items:center; font-weight:650; color:{NAVY};
}}
.package-head {{ color:{NAVY}; font-size:1.08rem; font-weight:800; padding:6px 0 12px; }}

.result-wrap {{
    background: #F6F8FA;
    border: 1px solid #D9E1E8;
    border-radius: 16px;
    padding: 22px 24px 18px 24px;
    margin: 8px 0 18px 0;
}}
.result-numbers {{
    display:flex; justify-content:space-between; align-items:flex-end;
    font-weight:800; color:#003A6E; font-size:2.25rem; line-height:1;
}}
.result-labels {{
    display:flex; justify-content:space-between; color:#17324D;
    font-size:.9rem; margin-top:6px;
}}
.share-track {{
    position:relative; height:22px; width:100%; border-radius:999px;
    background:#FAC108; overflow:hidden; margin:18px 0 4px 0;
}}
.share-a {{ height:100%; background:#003A6E; }}
.share-marker {{
    position:absolute; top:0; width:4px; height:100%;
    background:#FAC108; transform:translateX(-2px);
}}
.delta-card {{
    background:#FFF8DF; border-left:5px solid #FAC108;
    border-radius:8px; padding:14px 16px; min-height:92px;
}}
.delta-big {{ color:#003A6E; font-weight:800; font-size:1.65rem; }}

button[data-baseweb="tab"] p {{
    font-size: 19px !important;
    font-weight: 600 !important;
}}

button[data-baseweb="tab"] {{
    padding: 12px 18px !important;
}}

/* Package dropdowns: no red border */
div[data-baseweb="select"] > div {{
 border-color:#D9E1E8 !important;
 box-shadow:none !important;
 outline:none !important;
}}
div[data-baseweb="select"] > div:hover {{
 border-color:#003A6E !important;
}}
div[data-baseweb="select"] > div:focus,
div[data-baseweb="select"] > div:focus-within {{
 border-color:#003A6E !important;
 box-shadow:0 0 0 1px #003A6E !important;
 outline:none !important;
}}
div[data-testid="stSelectbox"] [aria-invalid="true"] {{
 border-color:#D9E1E8 !important;
 box-shadow:none !important;
}}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    raw = pd.read_csv(DATA / "raw_utilities.csv")
    imp = pd.read_csv(DATA / "importances.csv")
    agg = pd.read_csv(DATA / "aggregate_utilities.csv")
    return raw, imp, agg

raw, imp, agg = load_data()
N = len(raw)

ATTRIBUTES = {
    "Neto plača": {
        "prefix": "Neto plača (razlika od trenutne plače)",
        "levels": ["-10%", "0", "+10%", "+20%"],
    },
    "Bonus": {
        "prefix": "Bonus (letno nagrajevanje)",
        "levels": ["0%", "5%", "10%", "15%"],
    },
    "Delo na daljavo": {
        "prefix": "Delo od doma/na daljavo (tedensko)",
        "levels": ["0 dni", "1 dan", "2 dni", "3 dni"],
    },
    "Dopust": {
        "prefix": "Dopust",
        "levels": ["22 dni", "25 dni", "28 dni", "30 dni"],
    },
    "Fleksibilni delavnik": {
        "prefix": "Fleksibilni delavnik",
        "levels": ["fiksen", "+/- 2uri", "fleksibilno razporejanje"],
    },
    "Vlaganje v razvoj": {
        "prefix": "Vlaganje v razvoj",
        "levels": [
            "osnovno",
            "mentorstvo + interna izobraževanja",
            "1500 EUR na leto za razvoj po izbiri",
            "1500 EUR + 5 dni za razvoj po izbiri",
        ],
    },
    "Wellbeing in zdravje": {
        "prefix": "Wellbeing in zdravje",
        "levels": [
            "brez",
            "wellbeing budget",
            "specialisti + psihološka podpora",
            "razširjeni paket + wellbeing dnevi",
        ],
    },
}

def raw_col(prefix, level):
    target = f"{prefix}: {level} (Raw Utility)"
    if target not in raw.columns:
        raise KeyError(f"Manjka stolpec: {target}")
    return target

def package_utility(package):
    u = pd.Series(0.0, index=raw.index)
    for label, level in package.items():
        meta = ATTRIBUTES[label]
        u += raw[raw_col(meta["prefix"], level)]
    return u

def simulate(package_a, package_b, method):
    ua = package_utility(package_a)
    ub = package_utility(package_b)
    diff = (ua - ub).clip(-700, 700)
    if method == "Share of Preference (logit)":
        pa = 1.0 / (1.0 + (-diff).apply(math.exp))
        return float(pa.mean()), pa
    else:
        # deterministic first-choice; ties split 50/50
        pa = (ua > ub).astype(float)
        pa[ua == ub] = 0.5
        return float(pa.mean()), pa

def package_editor(title, key_prefix, defaults):
    st.subheader(title)
    out = {}
    for label, meta in ATTRIBUTES.items():
        default_level = defaults.get(label, meta["levels"][0])
        idx = meta["levels"].index(default_level)
        out[label] = st.selectbox(
            label,
            meta["levels"],
            index=idx,
            key=f"{key_prefix}_{label}",
        )
    return out


def result_hero(share_a, share_b):
    a = share_a * 100
    b = share_b * 100
    st.markdown(
        f"""
        <div class="result-wrap">
          <div class="result-numbers">
            <span>{a:.1f}%</span><span>{b:.1f}%</span>
          </div>
          <div class="result-labels">
            <span>PAKET A</span><span>PAKET B</span>
          </div>
          <div class="share-track">
            <div class="share-a" style="width:{a:.3f}%"></div>
            <div class="share-marker" style="left:{a:.3f}%"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def one_change_impact(base_a, base_b, attribute, new_level, method):
    changed = dict(base_a)
    changed[attribute] = new_level
    new_share = simulate(changed, base_b, method)[0]
    base_share = simulate(base_a, base_b, method)[0]
    return base_share, new_share, new_share - base_share


hc1, hc2 = st.columns([1, 7], vertical_alignment="center")
with hc1:
    if ICON.exists():
        st.image(str(ICON), width=40)
with hc2:
    st.title("Simulator zaposlitvenega paketa")
    st.caption(
        f"Pilotni Choice-Based Conjoint eksperiment ·  "
        "Sestavite dva paketa in primerjajte simulirani delež preference."
    )

st.markdown("""
### Kaj pomeni rezultat?

V raziskavi ljudi nismo spraševali samo, kaj jim je pri zaposlitvi pomembno.
Postavili smo jih pred **konkretne izbire med različnimi zaposlitvenimi paketi** –
na primer več plače, vendar manj dopusta, ali več dela od doma v zameno za nekaj drugega.

Iz več takšnih odločitev lahko ocenimo, **koliko vrednosti ljudje pripisujejo
posameznim elementom zaposlitvenega paketa in kakšne kompromise so pripravljeni sprejeti**.

Simulator te rezultate uporabi za primerjavo dveh paketov, ki ju sestavite sami.
Odstotek pokaže, **kateri od obeh paketov bi bil glede na odločitve sodelujočih
privlačnejši in za koliko**.

V tem pilotu so na izbire najbolj vplivali **plača, število dni dopusta in možnost
dela od doma**. Manjši vpliv so imeli bonus, fleksibilnost delovnika, razvoj ter
wellbeing in zdravje.

Pomembno: rezultat je odvisen tudi od tega, **kakšne razpone možnosti smo vključili
v eksperiment**.

*To je pilotni eksperiment s 36 sodelujočimi, zato rezultatov ne moremo posplošiti
na vse zaposlene v Sloveniji. Simulator prav tako ne napoveduje, ali bi nekdo
dejansko sprejel zaposlitveno ponudbo – pokaže relativno privlačnost dveh paketov
znotraj tega eksperimenta.*  
""")
st.write("")

tab1, tab2, tab3, tab4 = st.tabs(["Simulator", "Pomembnost atributov", "O eksperimentu", "Vizitka"])

with tab1:
    method = "Share of Preference (logit)"

    defaults_a = {
        "Neto plača": "0",
        "Bonus": "5%",
        "Delo na daljavo": "1 dan",
        "Dopust": "25 dni",
        "Fleksibilni delavnik": "+/- 2uri",
        "Vlaganje v razvoj": "mentorstvo + interna izobraževanja",
        "Wellbeing in zdravje": "wellbeing budget",
    }
    defaults_b = {
        "Neto plača": "+10%",
        "Bonus": "10%",
        "Delo na daljavo": "2 dni",
        "Dopust": "28 dni",
        "Fleksibilni delavnik": "fleksibilno razporejanje",
        "Vlaganje v razvoj": "1500 EUR na leto za razvoj po izbiri",
        "Wellbeing in zdravje": "specialisti + psihološka podpora",
    }

    st.markdown("### Oblikujte paketa")
    h0, h1, h2 = st.columns([1.35, 2.3, 2.3], gap="medium")
    with h0:
        st.markdown('<div class="package-head">Atribut</div>', unsafe_allow_html=True)
    with h1:
        st.markdown('<div class="package-head">Paket A</div>', unsafe_allow_html=True)
    with h2:
        st.markdown('<div class="package-head">Paket B</div>', unsafe_allow_html=True)

    package_a, package_b = {}, {}
    for i, (label, meta) in enumerate(ATTRIBUTES.items()):
        c0, c1, c2 = st.columns([1.35, 2.3, 2.3], gap="medium", vertical_alignment="center")
        with c0:
            st.markdown(f'<div class="attr-label">{label}</div>', unsafe_allow_html=True)
        with c1:
            package_a[label] = st.selectbox(
                f"{label} – A", meta["levels"],
                index=meta["levels"].index(defaults_a[label]),
                key=f"A_{i}", label_visibility="collapsed")
        with c2:
            package_b[label] = st.selectbox(
                f"{label} – B", meta["levels"],
                index=meta["levels"].index(defaults_b[label]),
                key=f"B_{i}", label_visibility="collapsed")

    share_a, respondent_pa = simulate(package_a, package_b, method)
    share_b = 1 - share_a

    st.divider()
    st.subheader("Simulirani delež preference")
    result_hero(share_a, share_b)

    st.markdown("### Kaj se zgodi, če spremenim samo en element?")
    st.write(
        "Izberite en atribut Paketa A in eno novo raven. Vsi ostali elementi obeh paketov "
        "ostanejo nespremenjeni."
    )

    q1, q2 = st.columns([1, 2], gap="medium")
    with q1:
        impact_attr = st.selectbox(
            "Spremeni atribut",
            list(ATTRIBUTES.keys()),
            key="impact_attribute"
        )
    current_level = package_a[impact_attr]
    possible_levels = [x for x in ATTRIBUTES[impact_attr]["levels"] if x != current_level]
    with q2:
        impact_level = st.selectbox(
            f"Nova raven (trenutno: {current_level})",
            possible_levels,
            key="impact_level"
        )

    base_share, new_share, delta = one_change_impact(
        package_a, package_b, impact_attr, impact_level, method
    )

    d1, d2, d3 = st.columns(3)
    with d1:
        st.markdown(
            f'<div class="delta-card"><b>Pred spremembo</b><div class="delta-big">{base_share:.1%}</div>'
            f'<span>Paket A</span></div>',
            unsafe_allow_html=True
        )
    with d2:
        st.markdown(
            f'<div class="delta-card"><b>Po spremembi</b><div class="delta-big">{new_share:.1%}</div>'
            f'<span>Paket A</span></div>',
            unsafe_allow_html=True
        )
    with d3:
        sign = "+" if delta >= 0 else ""
        st.markdown(
            f'<div class="delta-card"><b>Učinek spremembe</b>'
            f'<div class="delta-big">{sign}{delta*100:.1f} o. t.</div>'
            f'<span>simulirane preference</span></div>',
            unsafe_allow_html=True
        )

    st.markdown(
        f'<div class="note"><b>Primerjava:</b> Paket A: <b>{impact_attr}</b> '
        f'{current_level} → <b>{impact_level}</b>. Vsi drugi atributi ostanejo enaki.</div>',
        unsafe_allow_html=True
    )

with tab2:
    st.markdown("### Kaj je vplivalo na izbire?")

    # Relativna pomembnost atributov
    imp_plot = imp.copy()
    imp_plot["ImportancePct"] = imp_plot["Importance"] * 100
    imp_plot = imp_plot.sort_values("ImportancePct", ascending=True)

    fig_imp = go.Figure(
        go.Bar(
            x=imp_plot["ImportancePct"],
            y=imp_plot["Attribute"],
            orientation="h",
            marker_color=NAVY,
            text=imp_plot["ImportancePct"].map(lambda x: f"{x:.1f}%"),
            textposition="inside",
            insidetextanchor="end",
            textfont=dict(color=WHITE),
            hoverinfo="skip",
            hovertemplate=None,
        )
    )
    fig_imp.update_layout(
        title="Relativna pomembnost atributov",
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        font=dict(color=NAVY),
        title_font=dict(color=NAVY),
        showlegend=False,
        margin=dict(l=10, r=20, t=55, b=30),
        height=440,
    )
    fig_imp.update_xaxes(
        title="Relativna pomembnost (%)",
        color=NAVY,
        title_font=dict(color=NAVY),
        tickfont=dict(color=NAVY),
        gridcolor="#E9EEF2",
        zeroline=False,
    )
    fig_imp.update_yaxes(
        title=None,
        color=NAVY,
        tickfont=dict(color=NAVY),
        gridcolor=WHITE
    )
    st.plotly_chart(fig_imp, use_container_width=True, config={"displayModeBar": False})

    st.caption(
        "Pomembnost je odvisna od atributov in razponov ravni, testiranih v eksperimentu."
    )

    # Utilities: vsi atributi eden za drugim, brez dropdowna
    st.markdown("### Povprečne utilities po ravneh")

    for attribute_label, meta in ATTRIBUTES.items():
        prefix = meta["prefix"]
        subset = agg[agg["Attribute"] == prefix].copy()

        # Vrstni red ravni kot v eksperimentu; prva raven je na vrhu.
        level_order = meta["levels"]
        subset["Level"] = pd.Categorical(
            subset["Level"], categories=level_order, ordered=True
        )
        subset = subset.sort_values("Level", ascending=False)

        raw_levels = subset["Level"].astype(str).tolist()
        if prefix.startswith("Neto plača") or prefix.startswith("Bonus"):
            display_levels = [f"{level.replace('%', '').strip()}%" for level in raw_levels]
        else:
            display_levels = raw_levels

        fig_u = go.Figure(
            go.Bar(
                x=subset["Utility"],
                y=list(range(len(display_levels))),
                orientation="h",
                marker=dict(
                    color=NAVY,
                    line=dict(color=NAVY, width=0)
                ),
                text=subset["Utility"].map(lambda x: f"{x:.2f}"),
                textposition="outside",
                textfont=dict(color=NAVY, size=12),
                cliponaxis=False,
                hoverinfo="skip",
                hovertemplate=None,
            )
        )

        fig_u.update_layout(
            title=None,
            paper_bgcolor=WHITE,
            plot_bgcolor=WHITE,
            font=dict(color=NAVY),
            showlegend=False,
            margin=dict(l=190, r=55, t=60, b=25),
            height=max(250, 54 * len(subset) + 75),
            bargap=0.45,
        )

        # Enaka skala na vseh utility grafih, podobno referenčnemu Sawtooth prikazu.
        fig_u.update_xaxes(
            range=[-100, 100],
            tickmode="array",
            tickvals=[-100, -80, -60, -40, -20, 0, 20, 40, 60, 80, 100],
            side="top",
            title=None,
            color=NAVY,
            tickfont=dict(color=NAVY, size=11),
            gridcolor="#D9E1E8",
            gridwidth=1,
            zeroline=False,
            showline=True,
            linecolor="#D9E1E8",
            mirror=False,
        )
        fig_u.update_yaxes(
            title=None,
            color=NAVY,
            tickmode="array",
            tickvals=list(range(len(display_levels))),
            ticktext=display_levels,
            tickfont=dict(color=NAVY, size=14),
            showgrid=False,
            showline=True,
            linecolor="#D9E1E8",
        )

        # Naslov centriran nad dejanskim območjem stolpcev.

        fig_u.add_annotation(

            x=0.5,

            y=1.25,

            xref="x domain",

            yref="paper",

            text=f"<b>{attribute_label}</b>",

            showarrow=False,

            xanchor="center",

            font=dict(color=NAVY, size=15),

        )


        st.plotly_chart(
            fig_u,
            use_container_width=True,
            config={"displayModeBar": False, "staticPlot": True}
        )

with tab3:
    st.subheader("O pilotnem eksperimentu")
    st.markdown(
        f"""
**Vzorec:** N={N}  
**Metoda:** Choice-Based Conjoint (CBC)  
**Atributi:** 7  
**Namen:** demonstracija trade-offov pri oblikovanju zaposlitvenega paketa.

Respondenti so izbirali med hipotetičnimi zaposlitvenimi paketi, pri katerih so se
spreminjali plača, bonus, delo na daljavo, dopust, fleksibilnost, razvoj ter wellbeing in zdravje.

### Pomembne omejitve
- vzorec je pilotni in ni reprezentativen za slovenske zaposlene;
- hipotetična izbira ni enaka dejanskemu sprejemu zaposlitvene ponudbe;
- rezultat je pogojen z atributi in razponi ravni, vključenimi v eksperiment;
- simulator primerja relativno preferenco med prikazanimi paketi.
        """
    )

with tab4:
    st.markdown("## Vizitka")

    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        st.image(str(IMAGES / "primoz.png"), width="stretch")

    with col2:
        st.markdown("""
        **Ictus pomaga organizacijam sprejemati boljše odločitve na podlagi
        podatkov, raziskav in analitike.**

        Povezujemo organizacijske raziskave, **organizacijsko omrežno analizo (ONA)**,
        kadrovsko analitiko in napredne raziskovalne pristope, da iz podatkov
        ustvarjamo jasne in uporabne vpoglede.

        ONA omogoča pogled pod formalno organizacijsko strukturo – v dejanska
        omrežja sodelovanja, pretoka informacij in dostopa do znanja.

        Tudi ta conjoint simulator sledi istemu načelu: manj ugibanja,
        več razumevanja dejanskih odločitev ljudi.
        """)

    st.write("")
    st.markdown(
        "<hr style='border: 1px dashed #fac108; margin: 1.5rem 0;'>",
        unsafe_allow_html=True
    )

    links_html = """
    <div style="
        display:flex;
        justify-content:center;
        align-items:center;
        gap:2rem;
        flex-wrap:wrap;
        font-size:20px;
    ">
        <a href="https://www.ictus.si/" target="_blank">Spletna stran</a>
        <a href="mailto:info@ictus.si">Email</a>
        <a href="https://www.linkedin.com/in/primozdolzan" target="_blank">LinkedIn Primož</a>
        <a href="https://si.linkedin.com/company/ictus-ona" target="_blank">LinkedIn Ictus</a>
    </div>
    """

    st.markdown(links_html, unsafe_allow_html=True)    

st.divider()
st.caption("Pilotni raziskovalni demo · podatki iz CBC eksperimenta")
