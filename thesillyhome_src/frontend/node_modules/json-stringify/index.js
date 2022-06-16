'use strict';

module.exports = stringify;

var circular_stringify = require('json-stringify-safe');

// @param {Object} options
// - indent {Number}
// - offset {Number}
function stringify (object, replacer, indent, options) {
  options || (options = {});
  var str = circular_stringify(object, replacer, indent, options.decycler);

  if (!indent) {
    return str;
  }

  var offset = options.offset || 0;
  var spaces = space(offset);

  str = str
  .replace(/^|\n/g, function (match) {
    return match
      // carriage return
      ? match + spaces
      // Line start
      : spaces;
  })
  .slice(offset);

  return str;
}


function space (n) {
  var output = '';
  while (n --) {
    output += ' ';
  }

  return output;
}

// For testing
stringify._space = space;
