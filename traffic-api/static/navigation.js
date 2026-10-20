/* M01/M02 반응형 공통 메뉴. 관리자 인증정보를 다루지 않습니다. */
(function () {
    "use strict";

    const menuRoot = document.getElementById("sharedNavigation");
    if (!menuRoot) {
        return;
    }

    // M03: group navigation by actual page, not by overlapping feature names.
    const menuGroups = [
        {
            name: "경로 조회",
            items: [
                {name: "자동차 경로 검색", href: "/"},
                {name: "대표 경로 브리핑", href: "/#overviewSection"},
                {name: "이용 안내·FAQ", href: "/#helpSection"}
            ]
        },
        {
            name: "경로 지도",
            items: [
                {name: "지도에서 경로 확인", href: "/map"},
                {name: "관심 경로", href: "/map#favoriteRoutes"}
            ]
        },
        {
            name: "교통 뉴스·분석",
            items: [
                {name: "기사 검색·아카이브", href: "/news#historySection"},
                {name: "교통 비교 현황·데이터 안내", href: "/news#trafficDashboard"},
                {name: "시점별 교통 변화", href: "/news#trafficTrends"},
                {name: "CSV 다운로드", href: "/news#trafficExport"},
                {name: "뉴스 링크·읽기 모드", href: "/news#readingTools"}
            ]
        },
        {
            name: "관리자·운영",
            items: [
                {name: "기사 생성·검토·저장", href: "/admin"},
                {name: "API 사용 현황", href: "/admin#apiUsageSection"},
                {name: "기사 발행·보류", href: "/admin#publicationSection"},
                {name: "정기 수집 상태", href: "/admin#collectionRunsSection"},
                {name: "장애 기록·경고", href: "/admin#operationsSection"},
                {name: "운영 정책·공지 안내", href: "/admin#operatingGuideSection"}
            ]
        }
    ];

    const currentPath = window.location.pathname;
    const currentHash = window.location.hash;
    const mobileWidth = window.matchMedia("(max-width: 850px)");

    const inner = document.createElement("div");
    inner.className = "site-nav-inner";

    const brand = document.createElement("a");
    brand.className = "site-nav-brand";
    brand.href = "/";
    brand.textContent = "서울 도로교통정보";
    inner.appendChild(brand);

    const mobileButton = document.createElement("button");
    mobileButton.type = "button";
    mobileButton.className = "site-nav-toggle";
    mobileButton.textContent = "메뉴 열기";
    mobileButton.setAttribute("aria-controls", "sharedNavigationGroups");
    mobileButton.setAttribute("aria-expanded", "false");
    inner.appendChild(mobileButton);

    const groupContainer = document.createElement("div");
    groupContainer.className = "site-nav-groups";
    groupContainer.id = "sharedNavigationGroups";
    inner.appendChild(groupContainer);

    const triggers = [];
    const panels = [];

    function closePanels() {
        triggers.forEach(function (trigger) {
            trigger.setAttribute("aria-expanded", "false");
        });
        panels.forEach(function (panel) {
            panel.hidden = true;
        });
    }

    function showMobileMenu(open) {
        mobileButton.setAttribute("aria-expanded", String(open));
        mobileButton.textContent = open ? "메뉴 닫기" : "메뉴 열기";
        if (mobileWidth.matches) {
            groupContainer.hidden = !open;
        } else {
            groupContainer.hidden = false;
        }
        if (!open) {
            closePanels();
        }
    }

    menuGroups.forEach(function (group, index) {
        const groupWrapper = document.createElement("div");
        groupWrapper.className = "site-nav-group";

        const trigger = document.createElement("button");
        trigger.type = "button";
        trigger.className = "site-nav-trigger";
        trigger.textContent = group.name + " ▾";
        trigger.setAttribute("aria-controls", "siteNavPanel" + index);
        trigger.setAttribute("aria-expanded", "false");
        triggers.push(trigger);

        const panel = document.createElement("ul");
        panel.className = "site-nav-panel";
        panel.id = "siteNavPanel" + index;
        panel.hidden = true;
        panels.push(panel);

        group.items.forEach(function (item) {
            const li = document.createElement("li");
            li.className = "site-nav-item";
            if (item.planned) {
                const span = document.createElement("span");
                span.className = "site-nav-coming";
                span.textContent = item.name;
                const stateLabel = document.createElement("span");
                stateLabel.className = "site-nav-label";
                stateLabel.textContent = "준비 중";
                span.appendChild(stateLabel);
                li.appendChild(span);
            } else {
                const link = document.createElement("a");
                link.href = item.href;
                link.textContent = item.name;
                // 해시까지 일치하는 링크만 현재 위치로 표시합니다.
                // 현재 위치 표시는 접근성용이며 상시 파란 배경은 사용하지 않습니다.
                const linkUrl = new URL(item.href, window.location.origin);
                if (linkUrl.pathname === currentPath && linkUrl.hash === currentHash) {
                    link.setAttribute("aria-current", "page");
                }
                li.appendChild(link);
            }
            panel.appendChild(li);
        });

        trigger.addEventListener("click", function () {
            const wasOpen = trigger.getAttribute("aria-expanded") === "true";
            closePanels();
            if (!wasOpen) {
                trigger.setAttribute("aria-expanded", "true");
                panel.hidden = false;
            }
        });

        groupWrapper.appendChild(trigger);
        groupWrapper.appendChild(panel);
        groupContainer.appendChild(groupWrapper);
    });

    mobileButton.addEventListener("click", function () {
        showMobileMenu(mobileButton.getAttribute("aria-expanded") !== "true");
    });

    document.addEventListener("click", function (event) {
        if (!menuRoot.contains(event.target)) {
            closePanels();
        }
    });

    menuRoot.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closePanels();
            if (mobileWidth.matches && mobileButton.getAttribute("aria-expanded") === "true") {
                showMobileMenu(false);
                mobileButton.focus();
            } else {
                const focusedTrigger = triggers.find(function (button) {
                    return button.contains(document.activeElement);
                });
                if (focusedTrigger) {
                    focusedTrigger.focus();
                }
            }
        }
    });

    const onScreenChange = function () {
        showMobileMenu(false);
    };
    if (typeof mobileWidth.addEventListener === "function") {
        mobileWidth.addEventListener("change", onScreenChange);
    } else {
        mobileWidth.addListener(onScreenChange);
    }

    menuRoot.classList.add("site-nav");
    menuRoot.setAttribute("aria-label", "주요 메뉴");
    menuRoot.appendChild(inner);
    showMobileMenu(false);
})();
