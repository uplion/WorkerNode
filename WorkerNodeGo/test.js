const begin = new Date()
async function req(id) {
    const url = 'http://127.0.0.1:8081/api/v1/chat/completions';
    const data = {
        model: "gpt-3.5-turbo",
        messages: [
            {
                role: "user",
                content: "Hello"
            }
        ]
    };
    console.log("starting req", id)

    const res = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    const ans = await res.json();
    console.log(new Date().getTime() - begin.getTime(), ans.id)
    return ans
}

;(async function(){
Promise.all(Array(10).fill(0).map((e, i) => req(i)))
})();
