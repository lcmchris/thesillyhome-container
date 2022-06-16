# json-stringify [![NPM version](https://badge.fury.io/js/json-stringify.svg)](http://badge.fury.io/js/json-stringify) [![Build Status](https://travis-ci.org/kaelzhang/json-stringify.svg?branch=master)](https://travis-ci.org/kaelzhang/json-stringify) [![Dependency Status](https://gemnasium.com/kaelzhang/json-stringify.svg)](https://gemnasium.com/kaelzhang/json-stringify)

Like JSON.stringify, but enhanced, supports:

- offset for better typo when substituting the stringified json string.
- handle circular object, and doesn't blow up on circular refs.

## Install

```bash
$ npm install json-stringify --save
```

## Usage

```js
var stringify = require('json-stringify');
var array = [1, '2'];

stringify(array, null, 2, {
  offset: 4
});
```

You will get 

```json
[
------1,
------"2"
----]
```

#### We might encounter

So, if we have an template

```
{
  "foo": <bar>,
  "foo2": <bar2>
}
```

And there's an object `obj`

```js
var bar = stringify({
  bee: 'boo'
}, null, 2, {
  offset: 2
});

var bar2 = JSON.stringify({
  bee: 'boo'
}, null, 2);

var obj = {
  bar: bar,
  bar2: bar2
};
```

And the renderered result is:

```js
{
  "foo": {
    "bee": "boo" // well formatted
  },
  "foo2": {
  "bee": "boo" // a little ugly
}
}
```

You must found the difference.

#### Circular Object

```js
var circular = {};
circular.circular = circular;

var stringify = require('json-stringify');
console.log(stringify(circular, null, 2));
```

output:

```
{
  "circular": "[Circular ~]"
}
```


## `stringify(obj, replacer, indent, [options])`

The first three arguments are the same as to JSON.stringify. 

- `options.offset` defines the offset which described above
- `options.decycler` the decycler method of [json-stringify-safe](https://www.npmjs.com/package/json-stringify-safe)

The default decycler function returns the string '[Circular]'. If, for example, you pass in function(k,v){} (return nothing) then it will prune cycles. If you pass in function(k,v){ return {foo: 'bar'}}, then cyclical objects will always be represented as {"foo":"bar"} in the result.

## Licence

MIT
<!-- do not want to make nodeinit to complicated, you can edit this whenever you want. -->