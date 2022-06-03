import { readFile, readFileSync, writeFile } from 'fs'


export function get(request) {
    const data = readFileSync('.storage/config.yaml', 'utf-8')
    return {
        body: data
    }
    // readFile('.storage/config.yaml', 'utf8', (err, data) => {
    //     if (err) {
    //         console.error('oh no :(')
    //         console.error(err);
    //         return;
    //     }
    //     console.log(data);
    //     return { data }
    // });
}


// export function post(request) {
//     writeFile('../.storage/config.yaml', request, (err) => {
//         if (err) {
//             console.error(err);
//             return;
//         }
//         console.log(request);

//     });
// }



// export function get(request) {
//     return {
//         body: { hello: "world" }
//     }
// }
