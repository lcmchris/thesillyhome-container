'use strict';

var expect = require('chai').expect;
var stringify = require('../');

describe("stringify(str, options)", function(){
  it("test indent", function(done){
    var obj = {
      a: {
        b: 1,
        c: [1, "2", 3]
      },
      d: "123"
    };

    expect(
      JSON.stringify(obj, null, 2)
    ).to.equal(
      stringify(obj, null, 2)
    );

    done();
  });

  it("test offset", function(done){
    var obj = {
      a: {
        b: 0,
        c: [1, "2", 3]
      },
      d: "123"
    };

    var sub = {
      c: ["2", 1],
      d: 3
    };

    var sub_s = stringify(sub, null, 3, {
      offset: 6
    });

    var result = JSON.stringify(obj, null, 3).replace(/0/, sub_s);
    obj.a.b = sub;
    var expected = JSON.stringify(obj, null, 3);
    expect(result).to.equal(expected);
    done();
  });

  it("offset:3 only works if there is an indent", function(done){
    var a = {
      a: 1
    };

    expect(stringify(a, null, 0, {
      offset: 3
    })).to.equal('{"a":1}');
    done();
  });

  it("offset:3, indent:2", function(done){
    var a = {
      a: 1
    };

    var expected = '{\n'
      + '     "a": 1\n'
      + '   }';

    expect(stringify(a, null, 2, {
      offset: 3
    })).to.equal(expected);
    done();
  });

  it("will fail if circular object", function(done){
    var a = {}
    var obj = {
      a: a
    };
    a.a = a;

    try {
      stringify(obj);
    } catch(e) {
      expect(false).to.equal(true);
    }

    done();
  });
});