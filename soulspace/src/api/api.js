const API_BASE_URL = "http://localhost:5000";

// ---------------- AUTH ----------------

export const loginUser = async (data) => {
    const response = await fetch(`${API_BASE_URL}/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    });

    const result = await response.json();

    if (!response.ok) {
        throw new Error(result.error || "Login failed");
    }

    return result;
};

export const registerUser = async (data) => {
    const response = await fetch(`${API_BASE_URL}/register`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    });

    const result = await response.json();

    if (!response.ok) {
        throw new Error(result.error || "Registration failed");
    }

    return result;
};

// ---------------- JOURNAL ----------------

export const saveJournal = async (data, token) => {
    const response = await fetch(`${API_BASE_URL}/journal/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
    });

    const result = await response.json();

    if (!response.ok) {
        throw new Error(result.error || "Failed to save journal");
    }

    return result;
};