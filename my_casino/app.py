import streamlit as st
import random
import json
import os
import time

ADMIN_ID = "Admin"
ADMIN_PW = "yoko@10301"
MANAGER_ID = "manager"
MANAGER_PW = "yoko@10301"
MAX_LOAN_LIMIT = 500000
USER_DB_FILE = "users_db.json"
ROULETTE_RED = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]

# --- [DB 및 이자 처리 로직] ---
def process_loan_interest(user_data):
    loan = user_data.get("loan", 0)
    if loan <= 0:
        user_data["loan"] = 0
        return loan

    last_calc = user_data.get("last_interest_calc", 0)
    if last_calc == 0:
        return loan

    now = time.time()
    elapsed_minutes = int((now - last_calc) // 60)
    if elapsed_minutes >= 1:
        for _ in range(elapsed_minutes):
            loan = int(loan * 1.05)
        user_data["loan"] = loan
        user_data["last_interest_calc"] = last_calc + (elapsed_minutes * 60)
    return loan

def load_db():
    default_admin = {"password": ADMIN_PW, "balance": 10000000, "loan": 0, "loan_time": 0, "last_interest_calc": 0, "ban_until": 0, "baccarat_history": [], "is_active": True, "rig_mode": "NORMAL"}
    default_manager = {"password": MANAGER_PW, "balance": 5000000, "loan": 0, "loan_time": 0, "last_interest_calc": 0, "ban_until": 0, "baccarat_history": [], "is_active": True, "rig_mode": "NORMAL"}
    db = {"_settings": {"rig_mode": "NORMAL"}, ADMIN_ID: default_admin, MANAGER_ID: default_manager}

    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    db = loaded
        except Exception:
            pass

    for uid in list(db.keys()):
        if uid == "_settings": continue
        if isinstance(db[uid], dict):
            db[uid].setdefault("password", "1234")
            db[uid].setdefault("balance", 200000)
            db[uid].setdefault("loan", 0)
            db[uid].setdefault("loan_time", 0)
            db[uid].setdefault("last_interest_calc", 0)
            db[uid].setdefault("ban_until", 0)
            db[uid].setdefault("baccarat_history", [])
            db[uid].setdefault("is_active", True)
            db[uid].setdefault("rig_mode", "NORMAL")
            process_loan_interest(db[uid])
    save_db(db)
    return db

def save_db(db):
    try:
        with open(USER_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"DB 저장 오류: {e}")

# --- [세션 상태 초기화] ---
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "page" not in st.session_state:
    st.session_state.page = "lobby"
if "bet_target" not in st.session_state:
    st.session_state.bet_target = ""
if "bet_amount" not in st.session_state:
    st.session_state.bet_amount = 0

# --- [웹 앱 메인 레이아웃] ---
st.set_page_config(page_title="ROYAL PALACE CASINO", layout="wide")
db = load_db()

# 1. 로그인 / 회원가입 화면
if not st.session_state.user_id:
    st.title("👑 ROYAL PALACE CASINO")
    tab1, tab2 = st.tabs(["🔐 로그인", "📝 회원가입"])

    with tab1:
        login_id = st.text_input("아이디", key="login_id")
        login_pw = st.text_input("비밀번호", type="password", key="login_pw")
        if st.button("접속하기", type="primary"):
            if login_id in db and login_id != "_settings":
                udata = db[login_id]
                now = time.time()
                if not udata.get("is_active", True):
                    st.error("⛔ 정지된 계정입니다.")
                elif now < udata.get("ban_until", 0):
                    rem = int(udata["ban_until"] - now)
                    st.error(f"⛔ 파산으로 인한 계정 잠금 상태입니다. (남은 시간: {rem//60}분 {rem%60}초)")
                elif udata.get("password") == login_pw:
                    st.session_state.user_id = login_id
                    st.success(f"환영합니다, {login_id}님!")
                    st.rerun()
                else:
                    st.error("비밀번호가 일치하지 않습니다.")
            else:
                st.error("존재하지 않는 계정입니다.")

    with tab2:
        reg_id = st.text_input("신규 아이디", key="reg_id")
        reg_pw = st.text_input("신규 비밀번호", type="password", key="reg_pw")
        reg_pw_confirm = st.text_input("비밀번호 확인", type="password", key="reg_pw_confirm")
        if st.button("가입 신청"):
            if not reg_id or not reg_pw:
                st.warning("모든 필드를 입력해주세요.")
            elif reg_id in db or reg_id in (ADMIN_ID, MANAGER_ID, "_settings"):
                st.error("사용할 수 없거나 이미 존재하는 아이디입니다.")
            elif reg_pw != reg_pw_confirm:
                st.error("비밀번호가 일치하지 않습니다.")
            else:
                db[reg_id] = {"password": reg_pw, "balance": 200000, "loan": 0, "loan_time": 0, "last_interest_calc": 0, "ban_until": 0, "baccarat_history": [], "is_active": True, "rig_mode": "NORMAL"}
                save_db(db)
                st.success("회원가입이 완료되었습니다! 로그인 탭에서 접속하세요.")

# 2. 메인 카지노 서비스 화면
else:
    uid = st.session_state.user_id
    udata = db[uid]
    process_loan_interest(udata)

    # 사이드바 (사용자 정보 및 메뉴)
    with st.sidebar:
        st.header(f"👤 [{uid}] 님")
        st.metric("보유 머니", f"{udata['balance']:,} P")
        st.metric("사채 빚", f"{udata['loan']:,} P")
        st.divider()

        if st.button("🏛️ 게임 로비", use_container_width=True):
            st.session_state.page = "lobby"
            st.rerun()
        if st.button("💀 사채 / 대출 / 파산", use_container_width=True):
            st.session_state.page = "loan"
            st.rerun()

        if uid in (ADMIN_ID, MANAGER_ID):
            if st.button("🛠️ 관리자 패널", use_container_width=True):
                st.session_state.page = "admin"
                st.rerun()

        if st.button("🚪 로그아웃", use_container_width=True):
            st.session_state.user_id = None
            st.rerun()

    # 중앙 메인 화면 라우팅
    if st.session_state.page == "lobby":
        st.title("🎲 게임 선택")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🎲 주사위 홀짝")
            st.write("1.95배당 / 50:50 게임")
            if st.button("입장하기 (홀짝)"):
                st.session_state.page = "holjjak"
                st.rerun()

            st.subheader("🎡 멀티 룰렛")
            st.write("RED / BLACK 2.0배당")
            if st.button("입장하기 (룰렛)"):
                st.session_state.page = "roulette"
                st.rerun()

        with c2:
            st.subheader("🎴 정통 바카라")
            st.write("Player / Banker / Tie")
            if st.button("입장하기 (바카라)"):
                st.session_state.page = "baccarat"
                st.rerun()

            st.subheader("🐌 달팽이 레이스")
            st.write("2.9배당 / 3두 경주")
            if st.button("입장하기 (달팽이)"):
                st.session_state.page = "snail"
                st.rerun()

    # 배팅 카트 레이아웃 컴포넌트
    def render_bet_cart(game_name):
        st.divider()
        st.subheader("🛒 배팅 설정")
        col_amt, col_action = st.columns([2, 1])
        with col_amt:
            b1, b2, b3, b4 = st.columns(4)
            if b1.button("+1만"): st.session_state.bet_amount += 10000
            if b2.button("+5만"): st.session_state.bet_amount += 50000
            if b3.button("+10만"): st.session_state.bet_amount += 100000
            if b4.button("MAX"): st.session_state.bet_amount = udata["balance"]
            if st.button("금액 초기화"): st.session_state.bet_amount = 0

            st.session_state.bet_amount = min(st.session_state.bet_amount, udata["balance"])
            st.info(f"선택 항목: **{st.session_state.bet_target or '미선택'}** | 배팅 금액: **{st.session_state.bet_amount:,} P**")

        with col_action:
            if st.button("🔥 배팅 진행 (BET)", type="primary", use_container_width=True):
                if not st.session_state.bet_target:
                    st.warning("배팅 항목을 선택하세요.")
                    return False
                if st.session_state.bet_amount <= 0:
                    st.warning("배팅 금액을 입력하세요.")
                    return False
                udata["balance"] -= st.session_state.bet_amount
                return True
        return False

    # 미니게임 1: 홀짝
    if st.session_state.page == "holjjak":
        st.title("🎲 주사위 홀짝")
        c1, c2 = st.columns(2)
        if c1.button("［ 홀 ］", use_container_width=True): st.session_state.bet_target = "홀"
        if c2.button("［ 짝 ］", use_container_width=True): st.session_state.bet_target = "짝"

        if render_bet_cart("홀짝"):
            rig = udata.get("rig_mode", "NORMAL")
            if rig == "FORCE_WIN":
                res = st.session_state.bet_target
            elif rig == "FORCE_LOSE":
                res = "짝" if st.session_state.bet_target == "홀" else "홀"
            else:
                res = "홀" if random.randint(1, 6) % 2 != 0 else "짝"

            if st.session_state.bet_target == res:
                win = int(st.session_state.bet_amount * 1.95)
                udata["balance"] += win
                st.balloons()
                st.success(f"결과: [{res}] | 승리! {win:,} P 획득!")
            else:
                st.error(f"결과: [{res}] | 패배하셨습니다.")
            save_db(db)

    # 미니게임 2: 바카라
    elif st.session_state.page == "baccarat":
        st.title("🎴 정통 바카라")
        c1, c2, c3 = st.columns(3)
        if c1.button("PLAYER (2.0x)", use_container_width=True): st.session_state.bet_target = "Player"
        if c2.button("TIE (8.0x)", use_container_width=True): st.session_state.bet_target = "Tie"
        if c3.button("BANKER (1.95x)", use_container_width=True): st.session_state.bet_target = "Banker"

        if render_bet_cart("바카라"):
            rig = udata.get("rig_mode", "NORMAL")
            if rig == "FORCE_WIN": winner = st.session_state.bet_target
            elif rig == "FORCE_LOSE": winner = "Banker" if st.session_state.bet_target == "Player" else "Player"
            else:
                p, b = random.randint(0, 9), random.randint(0, 9)
                winner = "Player" if p > b else ("Banker" if b > p else "Tie")

            udata["baccarat_history"].append(winner)
            if st.session_state.bet_target == winner:
                rate = 2.0 if winner == "Player" else (1.95 if winner == "Banker" else 8.0)
                win = int(st.session_state.bet_amount * rate)
                udata["balance"] += win
                st.balloons()
                st.success(f"우승: [{winner}] | 승리! {win:,} P 획득!")
            else:
                st.error(f"우승: [{winner}] | 패배하셨습니다.")
            save_db(db)

        st.caption("최근 경기 기록: " + " - ".join(udata["baccarat_history"][-10:]))

    # 미니게임 3: 룰렛
    elif st.session_state.page == "roulette":
        st.title("🎡 멀티 룰렛")
        c1, c2 = st.columns(2)
        if c1.button("RED (2.0x)", use_container_width=True): st.session_state.bet_target = "RED"
        if c2.button("BLACK (2.0x)", use_container_width=True): st.session_state.bet_target = "BLACK"

        if render_bet_cart("룰렛"):
            rig = udata.get("rig_mode", "NORMAL")
            num = 1 if (rig == "FORCE_WIN" and st.session_state.bet_target == "RED") or (rig == "FORCE_LOSE" and st.session_state.bet_target == "BLACK") else 2
            color = "RED" if num in ROULETTE_RED else "BLACK"

            if st.session_state.bet_target == color:
                win = int(st.session_state.bet_amount * 2.0)
                udata["balance"] += win
                st.balloons()
                st.success(f"결과: [{num} {color}] | 승리! {win:,} P 획득!")
            else:
                st.error(f"결과: [{num} {color}] | 패배하셨습니다.")
            save_db(db)

    # 미니게임 4: 달팽이 레이스
    elif st.session_state.page == "snail":
        st.title("🐌 달팽이 레이스")
        c1, c2, c3 = st.columns(3)
        if c1.button("1번 달팽이", use_container_width=True): st.session_state.bet_target = "1번 달팽이"
        if c2.button("2번 달팽이", use_container_width=True): st.session_state.bet_target = "2번 달팽이"
        if c3.button("3번 달팽이", use_container_width=True): st.session_state.bet_target = "3번 달팽이"

        if render_bet_cart("달팽이"):
            rig = udata.get("rig_mode", "NORMAL")
            target_num = int(st.session_state.bet_target[0])
            if rig == "FORCE_WIN": winner_num = target_num
            elif rig == "FORCE_LOSE": winner_num = (target_num % 3) + 1
            else: winner_num = random.randint(1, 3)

            winner = f"{winner_num}번 달팽이"
            if st.session_state.bet_target == winner:
                win = int(st.session_state.bet_amount * 2.9)
                udata["balance"] += win
                st.balloons()
                st.success(f"우승: [{winner}] | 승리! {win:,} P 획득!")
            else:
                st.error(f"우승: [{winner}] | 패배하셨습니다.")
            save_db(db)

    # 대출 및 파산 창구
    elif st.session_state.page == "loan":
        st.title("💀 ROYAL LOAN SERVICES")
        st.warning("⚠️ 대출 즉시 20% 이자 부과 | 1분당 5% 복리 | 1분간 상환 불가")

        amt = st.number_input("신청/상환 금액", min_value=0, step=10000)
        col_b, col_r = st.columns(2)

        with col_b:
            if st.button("💰 대출 받기", use_container_width=True):
                if udata["loan"] + amt > MAX_LOAN_LIMIT:
                    st.error(f"최대 한도({MAX_LOAN_LIMIT:,} P) 초과")
                elif amt > 0:
                    now = time.time()
                    udata["balance"] += amt
                    udata["loan"] += int(amt * 1.20)
                    udata["loan_time"] = now
                    udata["last_interest_calc"] = now
                    save_db(db)
                    st.success("대출 처리 완료!")
                    st.rerun()

        with col_r:
            if st.button("💵 대출 상환", use_container_width=True):
                now = time.time()
                if udata["loan"] > 0 and (now - udata["loan_time"]) < 60:
                    st.error("대출 후 1분간은 상환할 수 없습니다.")
                elif amt > udata["balance"]:
                    st.error("보유 머니가 부족합니다.")
                elif amt > 0:
                    repay = min(amt, udata["loan"])
                    udata["balance"] -= repay
                    udata["loan"] -= repay
                    if udata["loan"] == 0:
                        udata["loan_time"] = 0
                        udata["last_interest_calc"] = 0
                    save_db(db)
                    st.success("상환 완료!")
                    st.rerun()

        st.divider()
        st.subheader("💥 개인 파산 신청")
        if st.button("🔥 파산 신청하기", type="primary"):
            if uid in (ADMIN_ID, MANAGER_ID):
                st.error("관리자는 파산할 수 없습니다.")
            else:
                udata["balance"] = 0
                udata["loan"] = 0
                udata["loan_time"] = 0
                udata["last_interest_calc"] = 0
                udata["ban_until"] = time.time() + 1800
                save_db(db)
                st.session_state.user_id = None
                st.warning("파산 처리되었습니다. 30분간 접속이 금지됩니다.")
                st.rerun()

    # 관리자 / 매니저 패널 (매니저 권한 제한 및 어드민 전용 기능 적용)
    elif st.session_state.page == "admin" and uid in (ADMIN_ID, MANAGER_ID):
        st.title("🛠️ SYSTEM ADMINISTRATION")
        
        # 전체 유저 현황
        st.dataframe([{
            "ID": u, 
            "상태": "🟢 정상" if d.get("is_active", True) and time.time() >= d.get("ban_until", 0) else "🔴 정지됨",
            "잔액": f"{d.get('balance',0):,} P", 
            "사채": f"{d.get('loan',0):,} P",
            "확률모드": d.get("rig_mode","NORMAL")
        } for u, d in db.items() if u != "_settings"])

        # 매니저는 Admin 및 다른 매니저 조작 불가능 (일반 유저만 선택 가능)
        if uid == ADMIN_ID:
            selectable_users = [u for u in db.keys() if u not in (ADMIN_ID, "_settings")]
        else:
            selectable_users = [u for u in db.keys() if u not in (ADMIN_ID, MANAGER_ID, "_settings")]

        if not selectable_users:
            st.info("조작할 수 있는 대상 계정이 없습니다.")
        else:
            target_u = st.selectbox("대상 계정 선택", selectable_users)
            
            if target_u:
                st.write(f"현재 선택된 계정: **{target_u}**")
                
                # 1. 머니 지급 및 차압 (관리자 및 매니저 공통)
                st.subheader("💵 머니 지급 / 차압")
                adj_amt = st.number_input("지급/차압 금액", value=100000, step=10000)
                col_a, col_s = st.columns(2)
                with col_a:
                    if st.button("➕ 머니 지급", use_container_width=True):
                        db[target_u]["balance"] += adj_amt
                        save_db(db)
                        st.success(f"[{target_u}] 님에게 {adj_amt:,} P 지급 완료")
                        st.rerun()
                with col_s:
                    if st.button("➖ 머니 차압", use_container_width=True):
                        db[target_u]["balance"] = max(0, db[target_u]["balance"] - adj_amt)
                        save_db(db)
                        st.warning(f"[{target_u}] 님의 {adj_amt:,} P 차압 완료")
                        st.rerun()

                st.divider()

                # 2. 계정 정지 / 정지 해제 기능 (★ 어드민 전용)
                if uid == ADMIN_ID:
                    st.subheader("🚨 계정 제재 관리 (어드민 전용)")
                    col_ban1, col_ban2 = st.columns(2)
                    with col_ban1:
                        if st.button("🔴 계정 강제 정지", use_container_width=True):
                            db[target_u]["is_active"] = False
                            save_db(db)
                            st.error(f"[{target_u}] 계정을 영구 정지 처리했습니다.")
                            st.rerun()

                    with col_ban2:
                        if st.button("🟢 정지 해제 / 파산 풀기", use_container_width=True):
                            db[target_u]["is_active"] = True
                            db[target_u]["ban_until"] = 0
                            save_db(db)
                            st.success(f"[{target_u}] 계정의 정지를 해제했습니다.")
                            st.rerun()

                    st.divider()

                    # 3. 승률 조작 (★ 어드민 전용)
                    st.subheader("🎯 승률 조작 (Rigging)")
                    rig_option = st.radio("확률 모드 선택", ["NORMAL", "FORCE_WIN", "FORCE_LOSE"], horizontal=True)
                    if st.button("💾 확률 모드 저장"):
                        db[target_u]["rig_mode"] = rig_option
                        save_db(db)
                        st.success(f"[{target_u}] 님의 모드가 [{rig_option}] 로 변경되었습니다.")
                else:
                    st.info("💡 계정 제재(정지/해제) 및 승률 조작 권한은 어드민(Admin)에게만 부여되어 있습니다.")
