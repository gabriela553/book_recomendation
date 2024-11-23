async function registerUser() {
    const username = document.getElementById("registerUsername").value;
    const password = document.getElementById("registerPassword").value;

    try {
        const response = await fetch("/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Request failed: ${response.status} - ${errorText}`);
        }

        const result = await response.json();
        document.getElementById("registerResult").textContent = result.message || result.error;
    } catch (error) {
        console.error("Registration error:", error);
        document.getElementById("registerResult").textContent = "An error occurred: " + error.message;
    }
}

async function loginUser() {
    const username = document.getElementById("loginUsername").value;
    const password = document.getElementById("loginPassword").value;

    try {
        const response = await fetch("/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Request failed: ${response.status} - ${errorText}`);
        }

        const result = await response.json();
        document.getElementById("loginResult").textContent = result.message || result.error;
    } catch (error) {
        console.error("Login error:", error);
        document.getElementById("loginResult").textContent = "An error occurred: " + error.message;
    }
}