/* F18: browser-only route favorites. No API calls are made by this module. */
(function () {
    "use strict";
    const STORAGE_KEY = "seoul-traffic-favorites-v1";
    const LIMIT = 10;
    const form = document.getElementById("routeForm") || document.getElementById("mapRouteForm");
    const panel = document.getElementById("favoriteRoutes");
    if (!form || !panel) return;
    const originInput = form.querySelector("#origin");
    const destinationInput = form.querySelector("#destination");
    const list = panel.querySelector("#favoriteRouteList");
    const status = panel.querySelector("#favoriteRouteStatus");
    const save = panel.querySelector("#saveFavoriteRoute");
    if (!originInput || !destinationInput || !list || !status || !save) return;
    let favorites = [];
    let storageAvailable = true;

    function normalize(value) {
        return typeof value === "string" ? value.trim().replace(/\s+/g, " ") : "";
    }
    function validPair(origin, destination) {
        return origin.length >= 2 && destination.length >= 2 &&
            origin.length <= 100 && destination.length <= 100 &&
            origin.toLocaleLowerCase() !== destination.toLocaleLowerCase();
    }
    function keyFor(item) {
        return item.origin.toLocaleLowerCase() + "\u0000" + item.destination.toLocaleLowerCase();
    }
    function readFavorites() {
        try {
            const saved = window.localStorage.getItem(STORAGE_KEY);
            if (saved === null) return [];
            const raw = JSON.parse(saved);
            if (!Array.isArray(raw)) throw new Error("Invalid favorites format");
            const unique = new Set();
            const clean = [];
            raw.forEach(function (value) {
                if (!value || typeof value !== "object") return;
                const origin = normalize(value.origin);
                const destination = normalize(value.destination);
                const pair = { origin: origin, destination: destination };
                const key = keyFor(pair);
                if (!validPair(origin, destination) || unique.has(key) || clean.length >= LIMIT) return;
                unique.add(key);
                clean.push(pair);
            });
            return clean;
        } catch (error) {
            storageAvailable = false;
            status.textContent = "저장된 관심 경로를 읽을 수 없습니다. 기본 경로 조회는 계속 사용할 수 있습니다.";
            return [];
        }
    }
    function persist(next) {
        if (!storageAvailable) {
            status.textContent = "브라우저 저장소를 사용할 수 없습니다. 기본 경로 조회는 계속 사용할 수 있습니다.";
            return false;
        }
        try {
            window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
            favorites = next;
            return true;
        } catch (error) {
            storageAvailable = false;
            status.textContent = "브라우저에 경로를 저장할 수 없습니다. 저장 공간과 브라우저 설정을 확인하세요.";
            return false;
        }
    }
    function actionButton(text, action, index) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "favorite-action";
        button.dataset.action = action;
        button.dataset.index = String(index);
        button.textContent = text;
        return button;
    }
    function render() {
        list.replaceChildren();
        if (favorites.length === 0) {
            const empty = document.createElement("li");
            empty.textContent = "저장된 관심 경로가 없습니다.";
            empty.className = "favorite-empty";
            list.appendChild(empty);
            return;
        }
        favorites.forEach(function (item, index) {
            const entry = document.createElement("li");
            entry.className = "favorite-item";
            const label = document.createElement("span");
            label.className = "favorite-label";
            label.textContent = item.origin + " → " + item.destination;
            const actions = document.createElement("div");
            actions.className = "favorite-item-actions";
            actions.appendChild(actionButton("불러오기", "load", index));
            actions.appendChild(actionButton("삭제", "delete", index));
            entry.appendChild(label);
            entry.appendChild(actions);
            list.appendChild(entry);
        });
    }
    save.addEventListener("click", function () {
        const pair = { origin: normalize(originInput.value), destination: normalize(destinationInput.value) };
        if (!validPair(pair.origin, pair.destination)) {
            status.textContent = "출발지와 목적지는 서로 달라야 하며, 각각 2~100자로 입력하세요.";
            return;
        }
        if (favorites.some(function (item) { return keyFor(item) === keyFor(pair); })) {
            status.textContent = "이미 저장된 관심 경로입니다.";
            return;
        }
        if (favorites.length >= LIMIT) {
            status.textContent = "관심 경로는 최대 10개까지 저장할 수 있습니다.";
            return;
        }
        if (persist(favorites.concat([pair]))) {
            render();
            status.textContent = "관심 경로를 이 브라우저에 저장했습니다.";
        }
    });
    list.addEventListener("click", function (event) {
        const button = event.target.closest("button[data-action]");
        if (!button || !list.contains(button)) return;
        const index = Number(button.dataset.index);
        if (!Number.isInteger(index) || index < 0 || index >= favorites.length) return;
        const item = favorites[index];
        if (button.dataset.action === "load") {
            originInput.value = item.origin;
            destinationInput.value = item.destination;
            status.textContent = "경로를 불러왔습니다. 경로 조회 버튼을 눌러 현재 교통정보를 확인하세요.";
            if (form.id === "mapRouteForm") {
                document.getElementById("result").textContent = "경로를 불러왔습니다. 경로 표시 버튼을 눌러 현재 교통정보를 조회하세요.";
            }
        } else if (button.dataset.action === "delete") {
            if (persist(favorites.filter(function (_, i) { return i !== index; }))) {
                render();
                status.textContent = "선택한 관심 경로를 삭제했습니다.";
            }
        }
    });
    window.addEventListener("storage", function (event) {
        if (event.key === STORAGE_KEY && storageAvailable) {
            favorites = readFavorites();
            render();
        }
    });
    favorites = readFavorites();
    render();
}());
