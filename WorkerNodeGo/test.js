async function req() {
    const url = 'http://localhost:8081/api/v1/chat/completions';
    const data = {
        model: "static",
        messages: [
            {
                role: "user",
                content: "Hello"
            }
        ]
    };

    const res = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    const ans = await res.json();
    console.log(ans.id)
    return ans
}

await Promise.all(Array(10).fill(0).map(() => req()))