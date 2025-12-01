import os, json, time, uuid, re
from datetime import datetime
from typing import Dict, List
import pandas as pd
import requests
import streamlit as st
import logging

# Setup logging at the top of your file
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="UnBarred", page_icon="⚖️", layout="wide")
VERSION = "2.0.4-sticky-bottom-jupyterhub"

# ------------------------------------------------------------
# Sticky bottom search bar INSIDE main (not fixed).
# This respects sidebar width in JupyterHub.
# ------------------------------------------------------------
st.markdown(
    """
<style>
/* sticky bottom bar wrapper */
.ub-bottom {
  position: sticky;
  bottom: 0;
  z-index: 50;
  background: var(--background-color);
  padding: 0.5rem 0 0.75rem 0;
  border-top: 1px solid rgba(255,255,255,0.08);
}

/* reduce form spacing */
.ub-bottom form { margin: 0; }
</style>
""",
    unsafe_allow_html=True,
)


# =========================
# County data
# =========================
def _as_county_label(name: str) -> str:
    n = name.strip()
    n = re.sub(r"\s+County$", "", n, flags=re.I)
    return f"{n} County"


def _to_slug(label: str) -> str:
    base = label.strip().lower()
    base = base.replace("&", "and")
    base = re.sub(r"'", "", base)
    base = re.sub(r"[\.]", "", base)
    base = re.sub(r"\s+", "-", base)
    base = re.sub(r"[^a-z0-9\-]", "-", base)
    base = re.sub(r"-+", "-", base).strip("-")
    if not base.endswith("-county"):
        base += "-county"
    return base


_FL_SRC = [
    "Alachua",
    "Baker",
    "Bay",
    "Bradford",
    "Brevard",
    "Broward",
    "Calhoun",
    "Charlotte",
    "Citrus",
    "Clay",
    "Collier",
    "Columbia",
    "DeSoto",
    "Dixie",
    "Duval",
    "Escambia",
    "Flagler",
    "Franklin",
    "Gadsden",
    "Gilchrist",
    "Glades",
    "Gulf",
    "Hamilton",
    "Hardee",
    "Hendry",
    "Hernando",
    "Highlands",
    "Hillsborough",
    "Holmes",
    "Indian River",
    "Jackson",
    "Jefferson",
    "Lafayette",
    "Lake",
    "Lee",
    "Leon",
    "Levy",
    "Liberty",
    "Madison",
    "Manatee",
    "Marion",
    "Martin",
    "Miami-Dade",
    "Monroe",
    "Nassau",
    "Okaloosa",
    "Okeechobee",
    "Orange",
    "Osceola",
    "Palm Beach",
    "Pasco",
    "Pinellas",
    "Polk",
    "Putnam",
    "Santa Rosa",
    "Sarasota",
    "Seminole",
    "St. Johns",
    "St. Lucie",
    "Sumter",
    "Suwannee",
    "Taylor",
    "Union",
    "Volusia",
    "Wakulla",
    "Walton",
    "Washington",
]
FL_LABELS = [_as_county_label(x) for x in _FL_SRC]

_GA_SRC = [
    "Appling County",
    "Atkinson County",
    "Bacon County",
    "Baker County",
    "Baldwin County",
    "Banks County",
    "Barrow County",
    "Bartow County",
    "Ben Hill County",
    "Berrien County",
    "Bibb County",
    "Bleckley County",
    "Brantley County",
    "Brooks County",
    "Bryan County",
    "Bulloch County",
    "Burke County",
    "Butts County",
    "Calhoun County",
    "Camden County",
    "Candler County",
    "Carroll County",
    "Catoosa County",
    "Charlton County",
    "Chatham County",
    "Chattahoochee County",
    "Chattooga County",
    "Cherokee County",
    "Clarke County",
    "Clay County",
    "Clayton County",
    "Clinch County",
    "Cobb County",
    "Coffee County",
    "Colquitt County",
    "Columbia County",
    "Cook County",
    "Coweta County",
    "Crawford County",
    "Crisp County",
    "Dade County",
    "Dawson County",
    "Decatur County",
    "DeKalb County",
    "Dodge County",
    "Dooly County",
    "Dougherty County",
    "Douglas County",
    "Early County",
    "Echols County",
    "Effingham County",
    "Elbert County",
    "Emanuel County",
    "Evans County",
    "Fannin County",
    "Fayette County",
    "Floyd County",
    "Forsyth County",
    "Franklin County",
    "Fulton County",
    "Gilmer County",
    "Glascock County",
    "Glynn County",
    "Gordon County",
    "Grady County",
    "Greene County",
    "Gwinnett County",
    "Habersham County",
    "Hall County",
    "Hancock County",
    "Haralson County",
    "Harris County",
    "Hart County",
    "Heard County",
    "Henry County",
    "Houston County",
    "Irwin County",
    "Jackson County",
    "Jasper County",
    "Jeff Davis County",
    "Jefferson County",
    "Jenkins County",
    "Johnson County",
    "Jones County",
    "Lamar County",
    "Lanier County",
    "Laurens County",
    "Lee County",
    "Liberty County",
    "Lincoln County",
    "Long County",
    "Lowndes County",
    "Lumpkin County",
    "Macon County",
    "Madison County",
    "Marion County",
    "McDuffie County",
    "McIntosh County",
    "Meriwether County",
    "Miller County",
    "Mitchell County",
    "Monroe County",
    "Montgomery County",
    "Morgan County",
    "Murray County",
    "Muscogee County",
    "Newton County",
    "Oconee County",
    "Oglethorpe County",
    "Paulding County",
    "Peach County",
    "Pickens County",
    "Pierce County",
    "Pike County",
    "Polk County",
    "Pulaski County",
    "Putnam County",
    "Quitman County",
    "Rabun County",
    "Randolph County",
    "Richmond County",
    "Rockdale County",
    "Schley County",
    "Screven County",
    "Seminole County",
    "Spalding County",
    "Stephens County",
    "Stewart County",
    "Sumter County",
    "Talbot County",
    "Taliaferro County",
    "Tattnall County",
    "Taylor County",
    "Telfair County",
    "Terrell County",
    "Thomas County",
    "Tift County",
    "Toombs County",
    "Towns County",
    "Treutlen County",
    "Troup County",
    "Turner County",
    "Twiggs County",
    "Union County",
    "Upson County",
    "Walker County",
    "Walton County",
    "Ware County",
    "Warren County",
    "Washington County",
    "Wayne County",
    "Webster County",
    "Wheeler County",
    "White County",
    "Whitfield County",
    "Wilcox County",
    "Wilbarger County",
    "Wilkinson County",
    "Worth County",
]
GA_LABELS = _GA_SRC[:]

_CA_SRC = [
    "Alameda",
    "Alpine",
    "Amador",
    "Butte",
    "Calaveras",
    "Colusa",
    "Contra Costa",
    "Del Norte",
    "El Dorado",
    "Fresno",
    "Glenn",
    "Humboldt",
    "Imperial",
    "Inyo",
    "Kern",
    "Kings",
    "Lake",
    "Lassen",
    "Los Angeles",
    "Madera",
    "Marin",
    "Mariposa",
    "Mendocino",
    "Merced",
    "Modoc",
    "Mono",
    "Monterey",
    "Napa",
    "Nevada",
    "Orange",
    "Placer",
    "Plumas",
    "Riverside",
    "Sacramento",
    "San Benito",
    "San Bernardino",
    "San Diego",
    "San Francisco",
    "San Joaquin",
    "San Luis Obispo",
    "San Mateo",
    "Santa Barbara",
    "Santa Clara",
    "Santa Cruz",
    "Shasta",
    "Sierra",
    "Siskiyou",
    "Solano",
    "Sonoma",
    "Stanislaus",
    "Sutter",
    "Tehama",
    "Trinity",
    "Tulare",
    "Tuolumne",
    "Ventura",
    "Yolo",
    "Yuba",
]
CA_LABELS = [_as_county_label(x) for x in _CA_SRC]

_TX_SRC = [
    "Anderson County",
    "Andrews County",
    "Angelina County",
    "Aransas County",
    "Archer County",
    "Armstrong County",
    "Atascosa County",
    "Austin County",
    "Bailey County",
    "Bandera County",
    "Bastrop County",
    "Baylor County",
    "Bee County",
    "Bell County",
    "Bexar County",
    "Blanco County",
    "Borden County",
    "Bosque County",
    "Bowie County",
    "Brazoria County",
    "Brazos County",
    "Brewster County",
    "Briscoe County",
    "Brooks County",
    "Brown County",
    "Burleson County",
    "Burnet County",
    "Caldwell County",
    "Calhoun County",
    "Callahan County",
    "Cameron County",
    "Camp County",
    "Carson County",
    "Cass County",
    "Castro County",
    "Chambers County",
    "Cherokee County",
    "Childress County",
    "Clay County",
    "Cochran County",
    "Coke County",
    "Coleman County",
    "Collin County",
    "Collingsworth County",
    "Colorado County",
    "Comal County",
    "Comanche County",
    "Concho County",
    "Cooke County",
    "Coryell County",
    "Cottle County",
    "Crane County",
    "Crockett County",
    "Crosby County",
    "Culberson County",
    "Dallam County",
    "Dallas County",
    "Dawson County",
    "Deaf Smith County",
    "Delta County",
    "Denton County",
    "DeWitt County",
    "Dickens County",
    "Dimmit County",
    "Donley County",
    "Duval County",
    "Eastland County",
    "Ector County",
    "Edwards County",
    "Ellis County",
    "El Paso County",
    "Erath County",
    "Falls County",
    "Fannin County",
    "Fayette County",
    "Fisher County",
    "Floyd County",
    "Foard County",
    "Fort Bend County",
    "Franklin County",
    "Freestone County",
    "Frio County",
    "Gaines County",
    "Galveston County",
    "Garza County",
    "Gillespie County",
    "Glasscock County",
    "Goliad County",
    "Gonzales County",
    "Gray County",
    "Grayson County",
    "Gregg County",
    "Grimes County",
    "Guadalupe County",
    "Hale County",
    "Hall County",
    "Hamilton County",
    "Hansford County",
    "Hardeman County",
    "Hardin County",
    "Harris County",
    "Harrison County",
    "Hartley County",
    "Haskell County",
    "Hays County",
    "Hemphill County",
    "Henderson County",
    "Hidalgo County",
    "Hill County",
    "Hockley County",
    "Hood County",
    "Hopkins County",
    "Houston County",
    "Howard County",
    "Hudspeth County",
    "Hunt County",
    "Hutchinson County",
    "Irion County",
    "Jack County",
    "Jackson County",
    "Jasper County",
    "Jeff Davis County",
    "Jefferson County",
    "Jim Hogg County",
    "Jim Wells County",
    "Johnson County",
    "Jones County",
    "Karnes County",
    "Kaufman County",
    "Kendall County",
    "Kenedy County",
    "Kent County",
    "Kerr County",
    "Kimble County",
    "King County",
    "Kinney County",
    "Kleberg County",
    "Knox County",
    "Lamar County",
    "Lamb County",
    "Lampasas County",
    "La Salle County",
    "Lavaca County",
    "Lee County",
    "Leon County",
    "Liberty County",
    "Limestone County",
    "Lipscomb County",
    "Live Oak County",
    "Llano County",
    "Loving County",
    "Lubbock County",
    "Lynn County",
    "McCulloch County",
    "McLennan County",
    "McMullen County",
    "Madison County",
    "Marion County",
    "Martin County",
    "Mason County",
    "Matagorda County",
    "Maverick County",
    "Medina County",
    "Menard County",
    "Midland County",
    "Milam County",
    "Mills County",
    "Mitchell County",
    "Montague County",
    "Montgomery County",
    "Moore County",
    "Morris County",
    "Motley County",
    "Nacogdoches County",
    "Navarro County",
    "Newton County",
    "Nolan County",
    "Nueces County",
    "Ochiltree County",
    "Oldham County",
    "Orange County",
    "Palo Pinto County",
    "Panola County",
    "Parker County",
    "Parmer County",
    "Pecos County",
    "Polk County",
    "Potter County",
    "Presidio County",
    "Rains County",
    "Randall County",
    "Reagan County",
    "Real County",
    "Red River County",
    "Reeves County",
    "Refugio County",
    "Roberts County",
    "Robertson County",
    "Rockwall County",
    "Runnels County",
    "Rusk County",
    "Sabine County",
    "San Augustine County",
    "San Jacinto County",
    "San Patricio County",
    "San Saba County",
    "Schleicher County",
    "Scurry County",
    "Shackelford County",
    "Shelby County",
    "Sherman County",
    "Smith County",
    "Somervell County",
    "Starr County",
    "Stephens County",
    "Sterling County",
    "Stonewall County",
    "Sutton County",
    "Swisher County",
    "Tarrant County",
    "Taylor County",
    "Terrell County",
    "Terry County",
    "Throckmorton County",
    "Titus County",
    "Tom Green County",
    "Travis County",
    "Trinity County",
    "Tyler County",
    "Upshur County",
    "Upton County",
    "Uvalde County",
    "Val Verde County",
    "Van Zandt County",
    "Victoria County",
    "Walker County",
    "Waller County",
    "Ward County",
    "Washington County",
    "Webb County",
    "Wharton County",
    "Wheeler County",
    "Wichita County",
    "Wilbarger County",
    "Willacy County",
    "Williamson County",
    "Winkler County",
    "Wise County",
    "Wood County",
    "Yoakum County",
    "Young County",
    "Zapata County",
    "Zavala County",
]
TX_LABELS = _TX_SRC[:]

STATES = {"ca": "California", "fl": "Florida", "ga": "Georgia", "tx": "Texas"}


def _labels_to_slug_map(labels: List[str]) -> Dict[str, str]:
    mapping = {}
    for lab in labels:
        label = _as_county_label(lab) if not lab.lower().endswith("county") else lab
        mapping[_to_slug(label)] = label
    return dict(sorted(mapping.items(), key=lambda kv: kv[1]))


COUNTY_LABELS_BY_STATE: Dict[str, Dict[str, str]] = {
    "fl": _labels_to_slug_map(FL_LABELS),
    "ga": _labels_to_slug_map(GA_LABELS),
    "ca": _labels_to_slug_map(CA_LABELS),
    "tx": _labels_to_slug_map(TX_LABELS),
}

# =========================
# Backend
# =========================
API_URL = os.getenv("UNBARRED_API", "").strip()
API_KEY = os.getenv("UNBARRED_API_KEY", "").strip()


def call_backend_api(payload: dict) -> dict:
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    r = requests.post(API_URL, json=payload, headers=headers, timeout=180)
    r.raise_for_status()
    return r.json()


# =========================
# Session
# =========================
ss = st.session_state
if "messages" not in ss:
    ss.messages = []
if "last_chunks" not in ss:
    ss.last_chunks = []
if "run_id" not in ss:
    ss.run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "-" + uuid.uuid4().hex[:6]

# =========================
# Sidebar
# =========================
with st.sidebar:
    st.header("UnBarred")
    st.caption(f"Run: {ss.run_id} • v{VERSION}")

    state_choices = st.multiselect(
        "State(s)",
        options=list(STATES.keys()),
        default=["ca"],
        format_func=lambda s: f"{STATES[s]} ({s.upper()})",
    )
    if len(state_choices) > 4:
        st.warning("Select up to 4 states. Using first 4.")
        state_choices = state_choices[:4]

    state_to_counties: Dict[str, List[str]] = {}
    for s in state_choices:
        st.subheader(f"{STATES[s]} counties")
        slug_to_label = COUNTY_LABELS_BY_STATE.get(s, {})
        label_to_slug = {v: k for k, v in slug_to_label.items()}
        all_labels = list(sorted(slug_to_label.values()))

        selected_labels = st.multiselect(
            "Choose counties (empty = ALL counties)",
            options=all_labels,
            default=[],
            placeholder="Type to search…",
            key=f"multiselect_{s}",
        )
        selected_slugs = [label_to_slug[lbl] for lbl in selected_labels]
        state_to_counties[s] = selected_slugs

    st.divider()
    st.subheader("Rule filters (optional)")
    penalty = st.checkbox("Penalty (Y)")
    obligation = st.checkbox("Obligation (Y)")
    permission = st.checkbox("Permission (Y)")
    prohibition = st.checkbox("Prohibition (Y)")

    st.divider()
    st.subheader("Readability ranges (always included)")
    fk_min, fk_max = st.slider("FK Grade (fk_grade)", 0.0, 80.0, (0.0, 80.0), 0.5)
    fre_min, fre_max = st.slider("FRE (fre)", -100.0, 120.0, (-100.0, 120.0), 1.0)
    wc_min, wc_max = st.slider("Word Count (wc)", 0, 2000, (0, 2000), 10)
    pctc_min, pctc_max = st.slider("Pct Complex (pct_complex)", 0, 100, (0, 100), 1)

    show_sources = st.checkbox("Show chunks table", value=True)

    if ss.last_chunks:
        df_dl = pd.DataFrame(
            [
                {
                    "section": c.get("section"),
                    "state": c.get("state"),
                    "county": c.get("county"),
                    "summary": c.get("summary"),
                    "score": c.get("score"),
                    "page": c.get("page"),
                    "raw_pdf_path": c.get("raw_pdf_path"),
                    "chunk_text": c.get("chunk_text"),
                    "fk_grade": c.get("fk_grade"),
                    "fre": c.get("fre"),
                    "wc": c.get("wc"),
                    "pct_complex": c.get("pct_complex"),
                    "penalty": c.get("penalty"),
                    "obligation": c.get("obligation"),
                    "permission": c.get("permission"),
                    "prohibition": c.get("prohibition"),
                }
                for c in ss.last_chunks
            ]
        )
        st.download_button(
            "Download chunks CSV",
            data=df_dl.to_csv(index=False).encode("utf-8"),
            file_name="unbarred_chunks.csv",
            mime="text/csv",
        )


# =========================
# Payload builder
# =========================
def build_locations(state_to_cty: Dict[str, List[str]]) -> List[dict]:
    locs = []
    for s, selected_slugs in state_to_cty.items():
        all_slugs = list(COUNTY_LABELS_BY_STATE.get(s, {}).keys())
        # Empty selection = ALL counties
        counties = selected_slugs if selected_slugs else all_slugs
        locs.append({"state": s, "county": counties})
    return locs


def build_payload(query_text: str) -> dict:
    filters = {
        "locations": build_locations(state_to_counties),
        "fk_grade": {"min": float(fk_min), "max": float(fk_max)},
        "fre": {"min": float(fre_min), "max": float(fre_max)},
        "wc": {"min": int(wc_min), "max": int(wc_max)},
        "pct_complex": {"min": int(pctc_min), "max": int(pctc_max)},
    }
    if penalty:
        filters["penalty"] = "Y"
    if obligation:
        filters["obligation"] = "Y"
    if permission:
        filters["permission"] = "Y"
    if prohibition:
        filters["prohibition"] = "Y"
    return {"query": query_text, "filters": filters}


# =========================
# Main
# =========================
st.title("UnBarred Search")

# Render history
for m in ss.messages:
    with st.chat_message(m["role"]):
        content = m["content"]
        if content and m["role"] == "assistant":
             content = content.replace("$", "\$")
        st.markdown(content)

# ---- Sticky bottom form in main ----
st.markdown('<div class="ub-bottom">', unsafe_allow_html=True)
with st.form("ub_search_form", clear_on_submit=True):
    user_text = st.text_input(
        "Ask about county ordinances…",
        placeholder="Ask about county ordinances…",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Search", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if submitted and user_text.strip():
    # 1. Log the User Query
    logger.info(f"User Query: '{user_text}' [RunID: {ss.run_id}]")
    ss.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    payload = build_payload(user_text)

    # 2. Log the Filters (Optional but helpful)
    logger.info(f"Filters Applied: {json.dumps(payload.get('filters'))} [RunID: {ss.run_id}]")

    with st.spinner("Running search…"):
        try:
            t0 = time.perf_counter()
            data = call_backend_api(payload)
            took_ms = int((time.perf_counter() - t0) * 1000)

            # 3. Log Success & Performance
            logger.info(f"Search Success: {len(data.get('chunks', []))} chunks found in {took_ms}ms [RunID: {ss.run_id}]")

        except requests.HTTPError as e:
            # 4. Log Errors
            logger.error(f"Backend Error: {str(e)} [RunID: {ss.run_id}]")
            st.error(f"Backend error: {e}\n\n{getattr(e.response, 'text', '')}")
            st.stop()
        except Exception as e:
            logger.error(f"Unexpected Error: {str(e)} [RunID: {ss.run_id}]")
            st.error(str(e))
            st.stop()

    ss.last_chunks = data.get("chunks", [])

    with st.chat_message("assistant"):
        response_text = data.get("response", "")
        
        # Simple fix: Escape dollar signs to prevent accidental LaTeX rendering
        # This replaces "$" with "\$" so Streamlit treats it as a literal dollar sign
        if response_text:
            response_text = response_text.replace("$", "\$")
            
        st.markdown(response_text)

        csv_file = data.get("csv_file")
        st.caption(f"CSV filename on server: {csv_file if csv_file else 'None'}")
        st.caption(
            f"Latency: {took_ms} ms • mode={data.get('mode')} • hits={len(ss.last_chunks)}"
        )

        if show_sources:
            if not ss.last_chunks:
                st.warning("No high-confidence ordinances retrieved.")
            else:
                rows = [
                    {
                        "section": c.get("section"),
                        "state": c.get("state"),
                        "county": c.get("county"),
                        "summary": c.get("summary"),
                        "score": c.get("score"),
                        "page": c.get("page"),
                        "raw_pdf_path": c.get("raw_pdf_path"),
                    }
                    for c in ss.last_chunks
                ]
                st.dataframe(pd.DataFrame(rows), use_container_width=True)

                st.subheader("Chunk details")
                for i, c in enumerate(ss.last_chunks, start=1):
                    with st.expander(
                        f"{i}. {c.get('section')} ({c.get('state')}, {c.get('county')})"
                    ):
                        st.write("summary:", c.get("summary"))
                        st.write("score:", c.get("score"))
                        st.write("rerank_score:", c.get("rerank_score"))
                        st.write(
                            "page → end_page:", c.get("page"), "→", c.get("end_page")
                        )
                        st.write(
                            "rule tags:",
                            {
                                "penalty": c.get("penalty"),
                                "obligation": c.get("obligation"),
                                "permission": c.get("permission"),
                                "prohibition": c.get("prohibition"),
                            },
                        )
                        st.write(
                            "readability:",
                            {
                                "fk_grade": c.get("fk_grade"),
                                "fre": c.get("fre"),
                                "wc": c.get("wc"),
                                "pct_complex": c.get("pct_complex"),
                            },
                        )
                        st.write("raw_pdf_path:", c.get("raw_pdf_path"))
                        st.write("chunk_text:")
                        st.code(c.get("chunk_text", ""))

        st.divider()
        st.subheader("Payload sent")
        st.json(payload)

    ss.messages.append({"role": "assistant", "content": data.get("response", "")})
