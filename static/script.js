const form = document.getElementById("login-form");
const resultBox = document.getElementById("result-output");
const overlay = document.getElementById("loading-overlay");

let currentStage = "login";

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    resultBox.classList.add("hidden");
    resultBox.innerHTML = "";
    overlay.classList.remove("hidden");

    const formData = new FormData(form);
    const username = formData.get("username");
    const password = formData.get("password");
    const code = formData.get("code") || "";

    const body = {
        username,
        password,
    };

    if ((currentStage === "login" && code) || (currentStage === "2fa")) {
        body["two_factor_code"] = code;
    } else if (currentStage === "email") {
        body["auth_code"] = code;
    }

    try {
        const res = await fetch("/get_ticket", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        const data = await res.json();
        overlay.classList.add("hidden");
        console.log(data);

        if (data.status === "ok") {
            // const blob = new Blob([Uint8Array.from(data.info.data)], { type: "application/zip" });
            resultBox.innerHTML = `<p style="color: green;">Logged In to Steam successfully... Loading data...</p>`;
            resultBox.classList.remove("hidden");
            overlay.classList.add("hidden");
            await new Promise(r => setTimeout(r, 100));
            overlay.classList.remove("hidden");

            const ticket = data.ticket;
            try {
                // window.location = `/data?ticket=${ticket}`;
                // overlay.classList.add("hidden");
                const res = await fetch(`/data?ticket=${ticket}`);
                const disposition = res.headers.get("Content-Disposition");
                let filename = "mvsdata.zip";
                if (disposition) {
                    const m = disposition.match(/filename="?([^"]+)"?/i);
                    if (m) filename = m[1];
                }
                filename = `${Math.floor(Date.now() / 1000)}_${filename}`;
                overlay.classList.add("hidden");
                
                const profileData = await res.blob();
                const url = URL.createObjectURL(profileData);
                console.log(url);

                const a = document.createElement("a");
                a.href = url;
                a.download = filename;
                a.className = "download-btn";
                const button = document.createElement("button");
                
                button.innerHTML = `Download Your Data!`;
                a.appendChild(button);
                resultBox.innerHTML = a.outerHTML;
            } catch (err) {
                console.log(err);
                overlay.classList.add("hidden");
                resultBox.innerHTML = `<p style="color: red;">Unknown error downloading user data</p>`;
                resultBox.classList.remove("hidden");
            }
        } else if (data.status === "2fa" || data.status === "email") {
            currentStage = data.status;
            resultBox.innerHTML = `<p style="color: orange;">Enter the ${data.status === "2fa" ? "2FA" : "Email"} code and resubmit.</p>`;
        } else {
            resultBox.innerHTML = `<p style="color: red;">${data.error || data.detail || "An error occurred."}</p>`;
        }
        resultBox.classList.remove("hidden");
    } catch (err) {
        overlay.classList.add("hidden");
        resultBox.innerHTML = `<p style="color: red;">Unknown error</p>`;
        resultBox.classList.remove("hidden");
    }
});
