"use strict";

var _typeof = require("@babel/runtime/helpers/typeof");
var _vitest = require("vitest");
var ahooks = _interopRequireWildcard(require("."));
function _interopRequireWildcard(e, t) { if ("function" == typeof WeakMap) var r = new WeakMap(), n = new WeakMap(); return (_interopRequireWildcard = function _interopRequireWildcard(e, t) { if (!t && e && e.__esModule) return e; var o, i, f = { __proto__: null, "default": e }; if (null === e || "object" != _typeof(e) && "function" != typeof e) return f; if (o = t ? n : r) { if (o.has(e)) return o.get(e); o.set(e, f); } for (var _t in e) "default" !== _t && {}.hasOwnProperty.call(e, _t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, _t)) && (i.get || i.set) ? o(f, _t, i) : f[_t] = e[_t]); return f; })(e, t); }
(0, _vitest.describe)('ahooks', function () {
  (0, _vitest.test)('exports modules should be defined', function () {
    Object.keys(ahooks).forEach(function (module) {
      (0, _vitest.expect)(ahooks[module]).toBeDefined();
    });
  });
});