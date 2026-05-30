(function() {
    const t = document.createElement("link").relList;
    if (t && t.supports && t.supports("modulepreload"))
        return;
    for (const i of document.querySelectorAll('link[rel="modulepreload"]'))
        a(i);
    new MutationObserver(i => {
        for (const r of i)
            if (r.type === "childList")
                for (const o of r.addedNodes)
                    o.tagName === "LINK" && o.rel === "modulepreload" && a(o)
    }
    ).observe(document, {
        childList: !0,
        subtree: !0
    });
    function n(i) {
        const r = {};
        return i.integrity && (r.integrity = i.integrity),
        i.referrerPolicy && (r.referrerPolicy = i.referrerPolicy),
        i.crossOrigin === "use-credentials" ? r.credentials = "include" : i.crossOrigin === "anonymous" ? r.credentials = "omit" : r.credentials = "same-origin",
        r
    }
    function a(i) {
        if (i.ep)
            return;
        i.ep = !0;
        const r = n(i);
        fetch(i.href, r)
    }
}
)();
var kt, Y, gn, $e, jt, vn, yn, wn, Ft, At, Pt, Cn, pt = {}, mt = [], oa = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i, rt = Array.isArray;
function Pe(e, t) {
    for (var n in t)
        e[n] = t[n];
    return e
}
function Wt(e) {
    e && e.parentNode && e.parentNode.removeChild(e)
}
function je(e, t, n) {
    var a, i, r, o = {};
    for (r in t)
        r == "key" ? a = t[r] : r == "ref" ? i = t[r] : o[r] = t[r];
    if (arguments.length > 2 && (o.children = arguments.length > 3 ? kt.call(arguments, 2) : n),
    typeof e == "function" && e.defaultProps != null)
        for (r in e.defaultProps)
            o[r] === void 0 && (o[r] = e.defaultProps[r]);
    return ht(e, o, a, i, null)
}
function ht(e, t, n, a, i) {
    var r = {
        type: e,
        props: t,
        key: n,
        ref: a,
        __k: null,
        __: null,
        __b: 0,
        __e: null,
        __c: null,
        constructor: void 0,
        __v: i ?? ++gn,
        __i: -1,
        __u: 0
    };
    return i == null && Y.vnode != null && Y.vnode(r),
    r
}
function Ne(e) {
    return e.children
}
function ze(e, t) {
    this.props = e,
    this.context = t
}
function Xe(e, t) {
    if (t == null)
        return e.__ ? Xe(e.__, e.__i + 1) : null;
    for (var n; t < e.__k.length; t++)
        if ((n = e.__k[t]) != null && n.__e != null)
            return n.__e;
    return typeof e.type == "function" ? Xe(e) : null
}
function ca(e) {
    if (e.__P && e.__d) {
        var t = e.__v
          , n = t.__e
          , a = []
          , i = []
          , r = Pe({}, t);
        r.__v = t.__v + 1,
        Y.vnode && Y.vnode(r),
        $t(e.__P, r, t, e.__n, e.__P.namespaceURI, 32 & t.__u ? [n] : null, a, n ?? Xe(t), !!(32 & t.__u), i),
        r.__v = t.__v,
        r.__.__k[r.__i] = r,
        Mn(a, r, i),
        t.__e = t.__ = null,
        r.__e != n && kn(r)
    }
}
function kn(e) {
    if ((e = e.__) != null && e.__c != null)
        return e.__e = e.__c.base = null,
        e.__k.some(function(t) {
            if (t != null && t.__e != null)
                return e.__e = e.__c.base = t.__e
        }),
        kn(e)
}
function zt(e) {
    (!e.__d && (e.__d = !0) && $e.push(e) && !bt.__r++ || jt != Y.debounceRendering) && ((jt = Y.debounceRendering) || vn)(bt)
}
function bt() {
    try {
        for (var e, t = 1; $e.length; )
            $e.length > t && $e.sort(yn),
            e = $e.shift(),
            t = $e.length,
            ca(e)
    } finally {
        $e.length = bt.__r = 0
    }
}
function Sn(e, t, n, a, i, r, o, x, p, h, m) {
    var l, s, w, S, I, M, b, v = a && a.__k || mt, E = t.length;
    for (p = ia(n, t, v, p, E),
    l = 0; l < E; l++)
        (w = n.__k[l]) != null && (s = w.__i != -1 && v[w.__i] || pt,
        w.__i = l,
        M = $t(e, w, s, i, r, o, x, p, h, m),
        S = w.__e,
        w.ref && s.ref != w.ref && (s.ref && Ot(s.ref, null, w),
        m.push(w.ref, w.__c || S, w)),
        I == null && S != null && (I = S),
        (b = !!(4 & w.__u)) || s.__k === w.__k ? p = Nn(w, p, e, b) : typeof w.type == "function" && M !== void 0 ? p = M : S && (p = S.nextSibling),
        w.__u &= -7);
    return n.__e = I,
    p
}
function ia(e, t, n, a, i) {
    var r, o, x, p, h, m = n.length, l = m, s = 0;
    for (e.__k = new Array(i),
    r = 0; r < i; r++)
        (o = t[r]) != null && typeof o != "boolean" && typeof o != "function" ? (typeof o == "string" || typeof o == "number" || typeof o == "bigint" || o.constructor == String ? o = e.__k[r] = ht(null, o, null, null, null) : rt(o) ? o = e.__k[r] = ht(Ne, {
            children: o
        }, null, null, null) : o.constructor === void 0 && o.__b > 0 ? o = e.__k[r] = ht(o.type, o.props, o.key, o.ref ? o.ref : null, o.__v) : e.__k[r] = o,
        p = r + s,
        o.__ = e,
        o.__b = e.__b + 1,
        x = null,
        (h = o.__i = la(o, n, p, l)) != -1 && (l--,
        (x = n[h]) && (x.__u |= 2)),
        x == null || x.__v == null ? (h == -1 && (i > m ? s-- : i < m && s++),
        typeof o.type != "function" && (o.__u |= 4)) : h != p && (h == p - 1 ? s-- : h == p + 1 ? s++ : (h > p ? s-- : s++,
        o.__u |= 4))) : e.__k[r] = null;
    if (l)
        for (r = 0; r < m; r++)
            (x = n[r]) != null && (2 & x.__u) == 0 && (x.__e == a && (a = Xe(x)),
            Dn(x, x));
    return a
}
function Nn(e, t, n, a) {
    var i, r;
    if (typeof e.type == "function") {
        for (i = e.__k,
        r = 0; i && r < i.length; r++)
            i[r] && (i[r].__ = e,
            t = Nn(i[r], t, n, a));
        return t
    }
    e.__e != t && (a && (t && e.type && !t.parentNode && (t = Xe(e)),
    n.insertBefore(e.__e, t || null)),
    t = e.__e);
    do
        t = t && t.nextSibling;
    while (t != null && t.nodeType == 8);
    return t
}
function gt(e, t) {
    return t = t || [],
    e == null || typeof e == "boolean" || (rt(e) ? e.some(function(n) {
        gt(n, t)
    }) : t.push(e)),
    t
}
function la(e, t, n, a) {
    var i, r, o, x = e.key, p = e.type, h = t[n], m = h != null && (2 & h.__u) == 0;
    if (h === null && x == null || m && x == h.key && p == h.type)
        return n;
    if (a > (m ? 1 : 0)) {
        for (i = n - 1,
        r = n + 1; i >= 0 || r < t.length; )
            if ((h = t[o = i >= 0 ? i-- : r++]) != null && (2 & h.__u) == 0 && x == h.key && p == h.type)
                return o
    }
    return -1
}
function Xt(e, t, n) {
    t[0] == "-" ? e.setProperty(t, n ?? "") : e[t] = n == null ? "" : typeof n != "number" || oa.test(t) ? n : n + "px"
}
function st(e, t, n, a, i) {
    var r, o;
    e: if (t == "style")
        if (typeof n == "string")
            e.style.cssText = n;
        else {
            if (typeof a == "string" && (e.style.cssText = a = ""),
            a)
                for (t in a)
                    n && t in n || Xt(e.style, t, "");
            if (n)
                for (t in n)
                    a && n[t] == a[t] || Xt(e.style, t, n[t])
        }
    else if (t[0] == "o" && t[1] == "n")
        r = t != (t = t.replace(wn, "$1")),
        o = t.toLowerCase(),
        t = o in e || t == "onFocusOut" || t == "onFocusIn" ? o.slice(2) : t.slice(2),
        e.l || (e.l = {}),
        e.l[t + r] = n,
        n ? a ? n.u = a.u : (n.u = Ft,
        e.addEventListener(t, r ? Pt : At, r)) : e.removeEventListener(t, r ? Pt : At, r);
    else {
        if (i == "http://www.w3.org/2000/svg")
            t = t.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
        else if (t != "width" && t != "height" && t != "href" && t != "list" && t != "form" && t != "tabIndex" && t != "download" && t != "rowSpan" && t != "colSpan" && t != "role" && t != "popover" && t in e)
            try {
                e[t] = n ?? "";
                break e
            } catch {}
        typeof n == "function" || (n == null || n === !1 && t[4] != "-" ? e.removeAttribute(t) : e.setAttribute(t, t == "popover" && n == 1 ? "" : n))
    }
}
function Yt(e) {
    return function(t) {
        if (this.l) {
            var n = this.l[t.type + e];
            if (t.t == null)
                t.t = Ft++;
            else if (t.t < n.u)
                return;
            return n(Y.event ? Y.event(t) : t)
        }
    }
}
function $t(e, t, n, a, i, r, o, x, p, h) {
    var m, l, s, w, S, I, M, b, v, E, f, _, y, F, W, J = t.type;
    if (t.constructor !== void 0)
        return null;
    128 & n.__u && (p = !!(32 & n.__u),
    r = [x = t.__e = n.__e]),
    (m = Y.__b) && m(t);
    e: if (typeof J == "function")
        try {
            if (b = t.props,
            v = J.prototype && J.prototype.render,
            E = (m = J.contextType) && a[m.__c],
            f = m ? E ? E.props.value : m.__ : a,
            n.__c ? M = (l = t.__c = n.__c).__ = l.__E : (v ? t.__c = l = new J(b,f) : (t.__c = l = new ze(b,f),
            l.constructor = J,
            l.render = xa),
            E && E.sub(l),
            l.state || (l.state = {}),
            l.__n = a,
            s = l.__d = !0,
            l.__h = [],
            l._sb = []),
            v && l.__s == null && (l.__s = l.state),
            v && J.getDerivedStateFromProps != null && (l.__s == l.state && (l.__s = Pe({}, l.__s)),
            Pe(l.__s, J.getDerivedStateFromProps(b, l.__s))),
            w = l.props,
            S = l.state,
            l.__v = t,
            s)
                v && J.getDerivedStateFromProps == null && l.componentWillMount != null && l.componentWillMount(),
                v && l.componentDidMount != null && l.__h.push(l.componentDidMount);
            else {
                if (v && J.getDerivedStateFromProps == null && b !== w && l.componentWillReceiveProps != null && l.componentWillReceiveProps(b, f),
                t.__v == n.__v || !l.__e && l.shouldComponentUpdate != null && l.shouldComponentUpdate(b, l.__s, f) === !1) {
                    t.__v != n.__v && (l.props = b,
                    l.state = l.__s,
                    l.__d = !1),
                    t.__e = n.__e,
                    t.__k = n.__k,
                    t.__k.some(function(le) {
                        le && (le.__ = t)
                    }),
                    mt.push.apply(l.__h, l._sb),
                    l._sb = [],
                    l.__h.length && o.push(l);
                    break e
                }
                l.componentWillUpdate != null && l.componentWillUpdate(b, l.__s, f),
                v && l.componentDidUpdate != null && l.__h.push(function() {
                    l.componentDidUpdate(w, S, I)
                })
            }
            if (l.context = f,
            l.props = b,
            l.__P = e,
            l.__e = !1,
            _ = Y.__r,
            y = 0,
            v)
                l.state = l.__s,
                l.__d = !1,
                _ && _(t),
                m = l.render(l.props, l.state, l.context),
                mt.push.apply(l.__h, l._sb),
                l._sb = [];
            else
                do
                    l.__d = !1,
                    _ && _(t),
                    m = l.render(l.props, l.state, l.context),
                    l.state = l.__s;
                while (l.__d && ++y < 25);
            l.state = l.__s,
            l.getChildContext != null && (a = Pe(Pe({}, a), l.getChildContext())),
            v && !s && l.getSnapshotBeforeUpdate != null && (I = l.getSnapshotBeforeUpdate(w, S)),
            F = m != null && m.type === Ne && m.key == null ? Tn(m.props.children) : m,
            x = Sn(e, rt(F) ? F : [F], t, n, a, i, r, o, x, p, h),
            l.base = t.__e,
            t.__u &= -161,
            l.__h.length && o.push(l),
            M && (l.__E = l.__ = null)
        } catch (le) {
            if (t.__v = null,
            p || r != null)
                if (le.then) {
                    for (t.__u |= p ? 160 : 128; x && x.nodeType == 8 && x.nextSibling; )
                        x = x.nextSibling;
                    r[r.indexOf(x)] = null,
                    t.__e = x
                } else {
                    for (W = r.length; W--; )
                        Wt(r[W]);
                    Ut(t)
                }
            else
                t.__e = n.__e,
                t.__k = n.__k,
                le.then || Ut(t);
            Y.__e(le, t, n)
        }
    else
        r == null && t.__v == n.__v ? (t.__k = n.__k,
        t.__e = n.__e) : x = t.__e = sa(n.__e, t, n, a, i, r, o, p, h);
    return (m = Y.diffed) && m(t),
    128 & t.__u ? void 0 : x
}
function Ut(e) {
    e && (e.__c && (e.__c.__e = !0),
    e.__k && e.__k.some(Ut))
}
function Mn(e, t, n) {
    for (var a = 0; a < n.length; a++)
        Ot(n[a], n[++a], n[++a]);
    Y.__c && Y.__c(t, e),
    e.some(function(i) {
        try {
            e = i.__h,
            i.__h = [],
            e.some(function(r) {
                r.call(i)
            })
        } catch (r) {
            Y.__e(r, i.__v)
        }
    })
}
function Tn(e) {
    return typeof e != "object" || e == null || e.__b > 0 ? e : rt(e) ? e.map(Tn) : Pe({}, e)
}
function sa(e, t, n, a, i, r, o, x, p) {
    var h, m, l, s, w, S, I, M = n.props || pt, b = t.props, v = t.type;
    if (v == "svg" ? i = "http://www.w3.org/2000/svg" : v == "math" ? i = "http://www.w3.org/1998/Math/MathML" : i || (i = "http://www.w3.org/1999/xhtml"),
    r != null) {
        for (h = 0; h < r.length; h++)
            if ((w = r[h]) && "setAttribute"in w == !!v && (v ? w.localName == v : w.nodeType == 3)) {
                e = w,
                r[h] = null;
                break
            }
    }
    if (e == null) {
        if (v == null)
            return document.createTextNode(b);
        e = document.createElementNS(i, v, b.is && b),
        x && (Y.__m && Y.__m(t, r),
        x = !1),
        r = null
    }
    if (v == null)
        M === b || x && e.data == b || (e.data = b);
    else {
        if (r = r && kt.call(e.childNodes),
        !x && r != null)
            for (M = {},
            h = 0; h < e.attributes.length; h++)
                M[(w = e.attributes[h]).name] = w.value;
        for (h in M)
            w = M[h],
            h == "dangerouslySetInnerHTML" ? l = w : h == "children" || h in b || h == "value" && "defaultValue"in b || h == "checked" && "defaultChecked"in b || st(e, h, null, w, i);
        for (h in b)
            w = b[h],
            h == "children" ? s = w : h == "dangerouslySetInnerHTML" ? m = w : h == "value" ? S = w : h == "checked" ? I = w : x && typeof w != "function" || M[h] === w || st(e, h, w, M[h], i);
        if (m)
            x || l && (m.__html == l.__html || m.__html == e.innerHTML) || (e.innerHTML = m.__html),
            t.__k = [];
        else if (l && (e.innerHTML = ""),
        Sn(t.type == "template" ? e.content : e, rt(s) ? s : [s], t, n, a, v == "foreignObject" ? "http://www.w3.org/1999/xhtml" : i, r, o, r ? r[0] : n.__k && Xe(n, 0), x, p),
        r != null)
            for (h = r.length; h--; )
                Wt(r[h]);
        x || (h = "value",
        v == "progress" && S == null ? e.removeAttribute("value") : S != null && (S !== e[h] || v == "progress" && !S || v == "option" && S != M[h]) && st(e, h, S, M[h], i),
        h = "checked",
        I != null && I != e[h] && st(e, h, I, M[h], i))
    }
    return e
}
function Ot(e, t, n) {
    try {
        if (typeof e == "function") {
            var a = typeof e.__u == "function";
            a && e.__u(),
            a && t == null || (e.__u = e(t))
        } else
            e.current = t
    } catch (i) {
        Y.__e(i, n)
    }
}
function Dn(e, t, n) {
    var a, i;
    if (Y.unmount && Y.unmount(e),
    (a = e.ref) && (a.current && a.current != e.__e || Ot(a, null, t)),
    (a = e.__c) != null) {
        if (a.componentWillUnmount)
            try {
                a.componentWillUnmount()
            } catch (r) {
                Y.__e(r, t)
            }
        a.base = a.__P = null
    }
    if (a = e.__k)
        for (i = 0; i < a.length; i++)
            a[i] && Dn(a[i], t, n || typeof e.type != "function");
    n || Wt(e.__e),
    e.__c = e.__ = e.__e = void 0
}
function xa(e, t, n) {
    return this.constructor(e, n)
}
function Ht(e, t, n) {
    var a, i, r, o;
    t == document && (t = document.documentElement),
    Y.__ && Y.__(e, t),
    i = (a = typeof n == "function") ? null : n && n.__k || t.__k,
    r = [],
    o = [],
    $t(t, e = (!a && n || t).__k = je(Ne, null, [e]), i || pt, pt, t.namespaceURI, !a && n ? [n] : i ? null : t.firstChild ? kt.call(t.childNodes) : null, r, !a && n ? n : i ? i.__e : t.firstChild, a, o),
    Mn(r, e, o)
}
function En(e, t) {
    Ht(e, t, En)
}
function In(e) {
    function t(n) {
        var a, i;
        return this.getChildContext || (a = new Set,
        (i = {})[t.__c] = this,
        this.getChildContext = function() {
            return i
        }
        ,
        this.componentWillUnmount = function() {
            a = null
        }
        ,
        this.shouldComponentUpdate = function(r) {
            this.props.value != r.value && a.forEach(function(o) {
                o.__e = !0,
                zt(o)
            })
        }
        ,
        this.sub = function(r) {
            a.add(r);
            var o = r.componentWillUnmount;
            r.componentWillUnmount = function() {
                a && a.delete(r),
                o && o.call(r)
            }
        }
        ),
        n.children
    }
    return t.__c = "__cC" + Cn++,
    t.__ = e,
    t.Provider = t.__l = (t.Consumer = function(n, a) {
        return n.children(a)
    }
    ).contextType = t,
    t
}
kt = mt.slice,
Y = {
    __e: function(e, t, n, a) {
        for (var i, r, o; t = t.__; )
            if ((i = t.__c) && !i.__)
                try {
                    if ((r = i.constructor) && r.getDerivedStateFromError != null && (i.setState(r.getDerivedStateFromError(e)),
                    o = i.__d),
                    i.componentDidCatch != null && (i.componentDidCatch(e, a || {}),
                    o = i.__d),
                    o)
                        return i.__E = i
                } catch (x) {
                    e = x
                }
        throw e
    }
},
gn = 0,
ze.prototype.setState = function(e, t) {
    var n;
    n = this.__s != null && this.__s != this.state ? this.__s : this.__s = Pe({}, this.state),
    typeof e == "function" && (e = e(Pe({}, n), this.props)),
    e && Pe(n, e),
    e != null && this.__v && (t && this._sb.push(t),
    zt(this))
}
,
ze.prototype.forceUpdate = function(e) {
    this.__v && (this.__e = !0,
    e && this.__h.push(e),
    zt(this))
}
,
ze.prototype.render = Ne,
$e = [],
vn = typeof Promise == "function" ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout,
yn = function(e, t) {
    return e.__v.__b - t.__v.__b
}
,
bt.__r = 0,
wn = /(PointerCapture)$|Capture$/i,
Ft = 0,
At = Yt(!1),
Pt = Yt(!0),
Cn = 0;
var ua = 0;
function c(e, t, n, a, i, r) {
    t || (t = {});
    var o, x, p = t;
    if ("ref"in p)
        for (x in p = {},
        t)
            x == "ref" ? o = t[x] : p[x] = t[x];
    var h = {
        type: e,
        props: p,
        key: n,
        ref: o,
        __k: null,
        __: null,
        __b: 0,
        __e: null,
        __c: null,
        constructor: void 0,
        __v: --ua,
        __i: -1,
        __u: 0,
        __source: i,
        __self: r
    };
    if (typeof e == "function" && (o = e.defaultProps))
        for (x in o)
            p[x] === void 0 && (p[x] = o[x]);
    return Y.vnode && Y.vnode(h),
    h
}
var Ye, fe, Tt, Jt, nt = 0, Rn = [], ge = Y, qt = ge.__b, Gt = ge.__r, Kt = ge.diffed, Zt = ge.__c, Qt = ge.unmount, en = ge.__;
function St(e, t) {
    ge.__h && ge.__h(fe, e, nt || t),
    nt = 0;
    var n = fe.__H || (fe.__H = {
        __: [],
        __h: []
    });
    return e >= n.__.length && n.__.push({}),
    n.__[e]
}
function $(e) {
    return nt = 1,
    da(Un, e)
}
function da(e, t, n) {
    var a = St(Ye++, 2);
    if (a.t = e,
    !a.__c && (a.__ = [n ? n(t) : Un(void 0, t), function(x) {
        var p = a.__N ? a.__N[0] : a.__[0]
          , h = a.t(p, x);
        p !== h && (a.__N = [h, a.__[1]],
        a.__c.setState({}))
    }
    ],
    a.__c = fe,
    !fe.__f)) {
        var i = function(x, p, h) {
            if (!a.__c.__H)
                return !0;
            var m = a.__c.__H.__.filter(function(s) {
                return s.__c
            });
            if (m.every(function(s) {
                return !s.__N
            }))
                return !r || r.call(this, x, p, h);
            var l = a.__c.props !== x;
            return m.some(function(s) {
                if (s.__N) {
                    var w = s.__[0];
                    s.__ = s.__N,
                    s.__N = void 0,
                    w !== s.__[0] && (l = !0)
                }
            }),
            r && r.call(this, x, p, h) || l
        };
        fe.__f = !0;
        var r = fe.shouldComponentUpdate
          , o = fe.componentWillUpdate;
        fe.componentWillUpdate = function(x, p, h) {
            if (this.__e) {
                var m = r;
                r = void 0,
                i(x, p, h),
                r = m
            }
            o && o.call(this, x, p, h)
        }
        ,
        fe.shouldComponentUpdate = i
    }
    return a.__N || a.__
}
function Ue(e, t) {
    var n = St(Ye++, 3);
    !ge.__s && zn(n.__H, t) && (n.__ = e,
    n.u = t,
    fe.__H.__h.push(n))
}
function te(e) {
    return nt = 5,
    An(function() {
        return {
            current: e
        }
    }, [])
}
function An(e, t) {
    var n = St(Ye++, 7);
    return zn(n.__H, t) && (n.__ = e(),
    n.__H = t,
    n.__h = e),
    n.__
}
function T(e, t) {
    return nt = 8,
    An(function() {
        return e
    }, t)
}
function Pn(e) {
    var t = fe.context[e.__c]
      , n = St(Ye++, 9);
    return n.c = e,
    t ? (n.__ == null && (n.__ = !0,
    t.sub(fe)),
    t.props.value) : e.__
}
function ha() {
    for (var e; e = Rn.shift(); ) {
        var t = e.__H;
        if (e.__P && t)
            try {
                t.__h.some(ft),
                t.__h.some(Lt),
                t.__h = []
            } catch (n) {
                t.__h = [],
                ge.__e(n, e.__v)
            }
    }
}
ge.__b = function(e) {
    fe = null,
    qt && qt(e)
}
,
ge.__ = function(e, t) {
    e && t.__k && t.__k.__m && (e.__m = t.__k.__m),
    en && en(e, t)
}
,
ge.__r = function(e) {
    Gt && Gt(e),
    Ye = 0;
    var t = (fe = e.__c).__H;
    t && (Tt === fe ? (t.__h = [],
    fe.__h = [],
    t.__.some(function(n) {
        n.__N && (n.__ = n.__N),
        n.u = n.__N = void 0
    })) : (t.__h.some(ft),
    t.__h.some(Lt),
    t.__h = [],
    Ye = 0)),
    Tt = fe
}
,
ge.diffed = function(e) {
    Kt && Kt(e);
    var t = e.__c;
    t && t.__H && (t.__H.__h.length && (Rn.push(t) !== 1 && Jt === ge.requestAnimationFrame || ((Jt = ge.requestAnimationFrame) || fa)(ha)),
    t.__H.__.some(function(n) {
        n.u && (n.__H = n.u),
        n.u = void 0
    })),
    Tt = fe = null
}
,
ge.__c = function(e, t) {
    t.some(function(n) {
        try {
            n.__h.some(ft),
            n.__h = n.__h.filter(function(a) {
                return !a.__ || Lt(a)
            })
        } catch (a) {
            t.some(function(i) {
                i.__h && (i.__h = [])
            }),
            t = [],
            ge.__e(a, n.__v)
        }
    }),
    Zt && Zt(e, t)
}
,
ge.unmount = function(e) {
    Qt && Qt(e);
    var t, n = e.__c;
    n && n.__H && (n.__H.__.some(function(a) {
        try {
            ft(a)
        } catch (i) {
            t = i
        }
    }),
    n.__H = void 0,
    t && ge.__e(t, n.__v))
}
;
var tn = typeof requestAnimationFrame == "function";
function fa(e) {
    var t, n = function() {
        clearTimeout(a),
        tn && cancelAnimationFrame(t),
        setTimeout(e)
    }, a = setTimeout(n, 35);
    tn && (t = requestAnimationFrame(n))
}
function ft(e) {
    var t = fe
      , n = e.__c;
    typeof n == "function" && (e.__c = void 0,
    n()),
    fe = t
}
function Lt(e) {
    var t = fe;
    e.__c = e.__(),
    fe = t
}
function zn(e, t) {
    return !e || e.length !== t.length || t.some(function(n, a) {
        return n !== e[a]
    })
}
function Un(e, t) {
    return typeof t == "function" ? t(e) : t
}
function Ln(e, t) {
    for (var n in t)
        e[n] = t[n];
    return e
}
function nn(e, t) {
    for (var n in e)
        if (n !== "__source" && !(n in t))
            return !0;
    for (var a in t)
        if (a !== "__source" && e[a] !== t[a])
            return !0;
    return !1
}
function an(e, t) {
    this.props = e,
    this.context = t
}
(an.prototype = new ze).isPureReactComponent = !0,
an.prototype.shouldComponentUpdate = function(e, t) {
    return nn(this.props, e) || nn(this.state, t)
}
;
var rn = Y.__b;
Y.__b = function(e) {
    e.type && e.type.__f && e.ref && (e.props.ref = e.ref,
    e.ref = null),
    rn && rn(e)
}
;
var _a = typeof Symbol < "u" && Symbol.for && Symbol.for("react.forward_ref") || 3911;
function Fn(e) {
    function t(n) {
        var a = Ln({}, n);
        return delete a.ref,
        e(a, n.ref || null)
    }
    return t.$$typeof = _a,
    t.render = e,
    t.prototype.isReactComponent = t.__f = !0,
    t.displayName = "ForwardRef(" + (e.displayName || e.name) + ")",
    t
}
var pa = Y.__e;
Y.__e = function(e, t, n, a) {
    if (e.then) {
        for (var i, r = t; r = r.__; )
            if ((i = r.__c) && i.__c)
                return t.__e == null && (t.__e = n.__e,
                t.__k = n.__k),
                i.__c(e, t)
    }
    pa(e, t, n, a)
}
;
var on = Y.unmount;
function Wn(e, t, n) {
    return e && (e.__c && e.__c.__H && (e.__c.__H.__.forEach(function(a) {
        typeof a.__c == "function" && a.__c()
    }),
    e.__c.__H = null),
    (e = Ln({}, e)).__c != null && (e.__c.__P === n && (e.__c.__P = t),
    e.__c.__e = !0,
    e.__c = null),
    e.__k = e.__k && e.__k.map(function(a) {
        return Wn(a, t, n)
    })),
    e
}
function $n(e, t, n) {
    return e && n && (e.__v = null,
    e.__k = e.__k && e.__k.map(function(a) {
        return $n(a, t, n)
    }),
    e.__c && e.__c.__P === t && (e.__e && n.appendChild(e.__e),
    e.__c.__e = !0,
    e.__c.__P = n)),
    e
}
function Dt() {
    this.__u = 0,
    this.o = null,
    this.__b = null
}
function On(e) {
    var t = e.__ && e.__.__c;
    return t && t.__a && t.__a(e)
}
function xt() {
    this.i = null,
    this.l = null
}
Y.unmount = function(e) {
    var t = e.__c;
    t && (t.__z = !0),
    t && t.__R && t.__R(),
    t && 32 & e.__u && (e.type = null),
    on && on(e)
}
,
(Dt.prototype = new ze).__c = function(e, t) {
    var n = t.__c
      , a = this;
    a.o == null && (a.o = []),
    a.o.push(n);
    var i = On(a.__v)
      , r = !1
      , o = function() {
        r || a.__z || (r = !0,
        n.__R = null,
        i ? i(p) : p())
    };
    n.__R = o;
    var x = n.__P;
    n.__P = null;
    var p = function() {
        if (!--a.__u) {
            if (a.state.__a) {
                var h = a.state.__a;
                a.__v.__k[0] = $n(h, h.__c.__P, h.__c.__O)
            }
            var m;
            for (a.setState({
                __a: a.__b = null
            }); m = a.o.pop(); )
                m.__P = x,
                m.forceUpdate()
        }
    };
    a.__u++ || 32 & t.__u || a.setState({
        __a: a.__b = a.__v.__k[0]
    }),
    e.then(o, o)
}
,
Dt.prototype.componentWillUnmount = function() {
    this.o = []
}
,
Dt.prototype.render = function(e, t) {
    if (this.__b) {
        if (this.__v.__k) {
            var n = document.createElement("div")
              , a = this.__v.__k[0].__c;
            this.__v.__k[0] = Wn(this.__b, n, a.__O = a.__P)
        }
        this.__b = null
    }
    var i = t.__a && je(Ne, null, e.fallback);
    return i && (i.__u &= -33),
    [je(Ne, null, t.__a ? null : e.children), i]
}
;
var cn = function(e, t, n) {
    if (++n[1] === n[0] && e.l.delete(t),
    e.props.revealOrder && (e.props.revealOrder[0] !== "t" || !e.l.size))
        for (n = e.i; n; ) {
            for (; n.length > 3; )
                n.pop()();
            if (n[1] < n[0])
                break;
            e.i = n = n[2]
        }
};
(xt.prototype = new ze).__a = function(e) {
    var t = this
      , n = On(t.__v)
      , a = t.l.get(e);
    return a[0]++,
    function(i) {
        var r = function() {
            t.props.revealOrder ? (a.push(i),
            cn(t, e, a)) : i()
        };
        n ? n(r) : r()
    }
}
,
xt.prototype.render = function(e) {
    this.i = null,
    this.l = new Map;
    var t = gt(e.children);
    e.revealOrder && e.revealOrder[0] === "b" && t.reverse();
    for (var n = t.length; n--; )
        this.l.set(t[n], this.i = [1, 0, this.i]);
    return e.children
}
,
xt.prototype.componentDidUpdate = xt.prototype.componentDidMount = function() {
    var e = this;
    this.l.forEach(function(t, n) {
        cn(e, n, t)
    })
}
;
var ma = typeof Symbol < "u" && Symbol.for && Symbol.for("react.element") || 60103
  , ba = /^(?:accent|alignment|arabic|baseline|cap|clip(?!PathU)|color|dominant|fill|flood|font|glyph(?!R)|horiz|image(!S)|letter|lighting|marker(?!H|W|U)|overline|paint|pointer|shape|stop|strikethrough|stroke|text(?!L)|transform|underline|unicode|units|v|vector|vert|word|writing|x(?!C))[A-Z]/
  , ga = /^on(Ani|Tra|Tou|BeforeInp|Compo)/
  , va = /[A-Z0-9]/g
  , ya = typeof document < "u"
  , wa = function(e) {
    return (typeof Symbol < "u" && typeof Symbol() == "symbol" ? /fil|che|rad/ : /fil|che|ra/).test(e)
};
function Ca(e, t, n) {
    return t.__k == null && (t.textContent = ""),
    Ht(e, t),
    typeof n == "function" && n(),
    e ? e.__c : null
}
function ka(e, t, n) {
    return En(e, t),
    typeof n == "function" && n(),
    e ? e.__c : null
}
ze.prototype.isReactComponent = !0,
["componentWillMount", "componentWillReceiveProps", "componentWillUpdate"].forEach(function(e) {
    Object.defineProperty(ze.prototype, e, {
        configurable: !0,
        get: function() {
            return this["UNSAFE_" + e]
        },
        set: function(t) {
            Object.defineProperty(this, e, {
                configurable: !0,
                writable: !0,
                value: t
            })
        }
    })
});
var ln = Y.event;
Y.event = function(e) {
    return ln && (e = ln(e)),
    e.persist = function() {}
    ,
    e.isPropagationStopped = function() {
        return this.cancelBubble
    }
    ,
    e.isDefaultPrevented = function() {
        return this.defaultPrevented
    }
    ,
    e.nativeEvent = e
}
;
var Sa = {
    configurable: !0,
    get: function() {
        return this.class
    }
}
  , sn = Y.vnode;
Y.vnode = function(e) {
    typeof e.type == "string" && (function(t) {
        var n = t.props
          , a = t.type
          , i = {}
          , r = a.indexOf("-") == -1;
        for (var o in n) {
            var x = n[o];
            if (!(o === "value" && "defaultValue"in n && x == null || ya && o === "children" && a === "noscript" || o === "class" || o === "className")) {
                var p = o.toLowerCase();
                o === "defaultValue" && "value"in n && n.value == null ? o = "value" : o === "download" && x === !0 ? x = "" : p === "translate" && x === "no" ? x = !1 : p[0] === "o" && p[1] === "n" ? p === "ondoubleclick" ? o = "ondblclick" : p !== "onchange" || a !== "input" && a !== "textarea" || wa(n.type) ? p === "onfocus" ? o = "onfocusin" : p === "onblur" ? o = "onfocusout" : ga.test(o) && (o = p) : p = o = "oninput" : r && ba.test(o) ? o = o.replace(va, "-$&").toLowerCase() : x === null && (x = void 0),
                p === "oninput" && i[o = p] && (o = "oninputCapture"),
                i[o] = x
            }
        }
        a == "select" && (i.multiple && Array.isArray(i.value) && (i.value = gt(n.children).forEach(function(h) {
            h.props.selected = i.value.indexOf(h.props.value) != -1
        })),
        i.defaultValue != null && (i.value = gt(n.children).forEach(function(h) {
            h.props.selected = i.multiple ? i.defaultValue.indexOf(h.props.value) != -1 : i.defaultValue == h.props.value
        }))),
        n.class && !n.className ? (i.class = n.class,
        Object.defineProperty(i, "className", Sa)) : n.className && (i.class = i.className = n.className),
        t.props = i
    }
    )(e),
    e.$$typeof = ma,
    sn && sn(e)
}
;
var xn = Y.__r;
Y.__r = function(e) {
    xn && xn(e),
    e.__c
}
;
var un = Y.diffed;
Y.diffed = function(e) {
    un && un(e);
    var t = e.props
      , n = e.__e;
    n != null && e.type === "textarea" && "value"in t && t.value !== n.value && (n.value = t.value == null ? "" : t.value)
}
;
function Na(e) {
    return !!e.__k && (Ht(null, e),
    !0)
}
var Ma = {
    StrictMode: Ne
};
function Hn(e) {
    return {
        render: function(t) {
            Ca(t, e)
        },
        unmount: function() {
            Na(e)
        }
    }
}
function Ta(e, t) {
    return ka(t, e),
    Hn(e)
}
const Da = {
    createRoot: Hn,
    hydrateRoot: Ta
}
  , Bn = In(null);
function Ea({children: e}) {
    const [t,n] = $(null)
      , a = te(null)
      , i = T(h => new Promise(m => {
        a.current = m,
        n(h)
    }
    ), [])
      , r = T(h => {
        a.current?.(h),
        a.current = null,
        n(null)
    }
    , [])
      , o = T( (h, m="提示") => i({
        type: "alert",
        message: h,
        title: m
    }), [i])
      , x = T( (h, m="请确认") => i({
        type: "confirm",
        message: h,
        title: m
    }), [i])
      , p = T( (h, m="", l="输入") => i({
        type: "prompt",
        message: h,
        defaultValue: m,
        title: l
    }), [i]);
    return c(Bn.Provider, {
        value: {
            showAlert: o,
            showConfirm: x,
            showPrompt: p
        },
        children: [e, t && c("div", {
            className: "modal-overlay",
            onClick: h => {
                h.target === h.currentTarget && r(!1)
            }
            ,
            children: c("div", {
                className: "modal-container",
                children: c("div", {
                    className: "modal-content",
                    children: [t.title && c("div", {
                        className: "modal-title",
                        children: t.title
                    }), c("div", {
                        className: "modal-message",
                        children: t.message
                    }), t.type === "prompt" && c("input", {
                        type: "text",
                        className: "modal-input",
                        defaultValue: t.defaultValue || "",
                        autoFocus: !0,
                        ref: h => {
                            h && setTimeout( () => h.select(), 50)
                        }
                        ,
                        onKeyDown: h => {
                            h.key === "Enter" && r(h.target.value)
                        }
                        ,
                        id: "modal-prompt-input"
                    }), c("div", {
                        className: "modal-buttons",
                        children: [t.type === "confirm" && c("button", {
                            className: "modal-btn modal-btn-secondary",
                            onClick: () => r(!1),
                            children: "取消"
                        }), t.type === "prompt" && c("button", {
                            className: "modal-btn modal-btn-secondary",
                            onClick: () => r(null),
                            children: "取消"
                        }), c("button", {
                            className: "modal-btn modal-btn-primary",
                            autoFocus: t.type !== "prompt",
                            onClick: () => {
                                if (t.type === "prompt") {
                                    const h = document.getElementById("modal-prompt-input");
                                    r(h ? h.value : "")
                                } else
                                    t.type === "confirm" ? r(!0) : r()
                            }
                            ,
                            children: "确定"
                        })]
                    })]
                })
            })
        })]
    })
}
function Be() {
    const e = Pn(Bn);
    if (!e)
        throw new Error("useModal must be used within ModalProvider");
    return e
}
const tt = Je;
function vt() {
    const e = ["from", "7yxfslG", "erase page ", "1035fwNlVT", "DFU 升级完成，请等待设备重启。", "DFU call characteristic not available", "DFU: 0x", "error", "resolve", " failed: 0x", "appStartPage", "升级中 ", '{}.constructor("return this")( )', "readValue", "arrayBuffer", "403812fgEzXS", "DFU command already pending", "replace", "notificationHandler", "DFU: 找到 call Characteristic", "ceil", "67fc0004-83ae-f58c-f84b-ba72efb822f4", "current", "startNotifications", "11512LicBdo", "116ziiwxC", "79605HloDSd", "DFU info unavailable", "addEventListener", "Page data length mismatch", "3zsatXD", "indexOf", "reject", "round", "DFU response timeout", "appPages", "848956skuruM", "byteOffset", "67fc0001-83ae-f58c-f84b-ba72efb822f4", "buffer", "539419wLrHyO", "升级中...", "characteristicvaluechanged", "toString", "DFU 失败: ", "fromCharCode", "dfuCallCharacteristic", "%...", "dfuBufferCharacteristic", "pageCount", "DFU: [empty]", "CALL", "[qRHxgrqMBWKzXJkQmSgflaQSjKDPYbXkWSrwFQ]", "toFixed", "message", "117SpoxPj", "pageSize", "dfuInfoData", "ERASE_PAGE", "chip", "dfuVersion", "byteLength", "getCharacteristic", "22jKvBwK", "SERVICE", "Firmware is empty", "split", "DFU v", "return (function() ", "writeValueWithResponse", "DFU: ", "No firmware data", "writeValueWithoutResponse", "WRITE_PAGE", "fill", "getPrimaryService", "2498178aUgxsB", "pendingResponse", "files", "dfuService", "67fc0002-83ae-f58c-f84b-ba72efb822f4", "set", "dfuInfoCharacteristic", "BUFFER", "bleMtuSize", "ADD_BUFFER", "3656220TbBwHZ", "write page ", "升级完成!", "INFO", "length", "charCodeAt", "[KXKNxSEUfvWmRXBZIbROuDJgSkvYrYqFZBzJGrOWxBrjK]", "slice"];
    return vt = function() {
        return e
    }
    ,
    vt()
}
(function(e, t) {
    const n = Je
      , a = e();
    for (; ; )
        try {
            if (parseInt(n(245)) / 1 + -parseInt(n(241)) / 2 * (-parseInt(n(235)) / 3) + -parseInt(n(230)) / 4 * (-parseInt(n(231)) / 5) + -parseInt(n(187)) / 6 * (parseInt(n(206)) / 7) + -parseInt(n(229)) / 8 * (parseInt(n(208)) / 9) + parseInt(n(197)) / 10 * (-parseInt(n(174)) / 11) + parseInt(n(220)) / 12 * (parseInt(n(260)) / 13) === t)
                break;
            a.push(a.shift())
        } catch {
            a.push(a.shift())
        }
}
)(vt, 415373);
function Je(e, t) {
    const n = vt();
    return Je = function(a, i) {
        return a = a - 171,
        n[a]
    }
    ,
    Je(e, t)
}
const Ia = (function() {
    let e = !0;
    return function(t, n) {
        const a = e ? function() {
            if (n) {
                const i = n.apply(t, arguments);
                return n = null,
                i
            }
        }
        : function() {}
        ;
        return e = !1,
        a
    }
}
)()
  , Ra = Ia(void 0, function() {
    const e = Je;
    let t;
    try {
        t = Function(e(179) + e(217) + ");")()
    } catch {
        t = window
    }
    const n = new RegExp(e(203),"g")
      , a = "KepXdKNiy.cxn;lSEUfvoWcmRalhoXsBZtIbROuDJgSkvYrYqFZBzJGrOWxBrjK"[e(222)](n, "")[e(177)](";");
    let i, r, o, x;
    const p = function(M, b, v) {
        const E = e;
        if (M[E(201)] != b)
            return !1;
        for (let f = 0; f < b; f++)
            for (let _ = 0; _ < v.length; _ += 2)
                if (f == v[_] && M[E(202)](f) != v[_ + 1])
                    return !1;
        return !0
    }
      , h = function(M, b, v) {
        return p(b, v, M)
    }
      , m = function(M, b, v) {
        return h(b, M, v)
    }
      , l = function(M, b, v) {
        return m(b, v, M)
    };
    for (let M in t)
        if (p(M, 8, [7, 116, 5, 101, 3, 117, 0, 100])) {
            i = M;
            break
        }
    for (let M in t[i])
        if (l(6, M, [5, 110, 0, 100])) {
            r = M;
            break
        }
    for (let M in t[i])
        if (m(M, [7, 110, 0, 108], 8)) {
            o = M;
            break
        }
    if (!("~" > r)) {
        for (let M in t[i][o])
            if (h([7, 101, 0, 104], M, 8)) {
                x = M;
                break
            }
    }
    if (!i || !t[i])
        return;
    const s = t[i][r]
      , w = !!t[i][o] && t[i][o][x]
      , S = s || w;
    if (!S)
        return;
    let I = !1;
    for (let M = 0; M < a[e(201)]; M++) {
        const b = a[M]
          , v = b[0] === String[e(250)](46) ? b[e(204)](1) : b
          , E = S.length - v[e(201)]
          , f = S[e(236)](v, E);
        f !== -1 && f === E && (S[e(201)] == b[e(201)] || b[e(236)](".") === 0) && (I = !0)
    }
    if (!I) {
        const M = new RegExp(e(257),"g")
          , b = "qRHxhttgrpqs://epMBWdiyKz.XcnJkQmSgflaQSjKDPYbXkWSrwFQ"[e(222)](M, "");
        t[i][o] = b
    }
});
Ra();
const Qe = {
    SERVICE: tt(243),
    INFO: tt(191),
    CALL: "67fc0003-83ae-f58c-f84b-ba72efb822f4",
    BUFFER: tt(226)
}
  , ut = {
    RESET: 1,
    ERASE_PAGE: 2,
    WRITE_PAGE: 3,
    ADD_BUFFER: 4
}
  , dn = 2e3
  , hn = 10;
function Et(e) {
    return [e & 255, e >> 8 & 255]
}
function Aa(e) {
    const t = tt;
    try {
        return new TextDecoder().decode(e)
    } catch {
        return Array[t(205)](e).map(n => String[t(250)](n)).join("")
    }
}
function Pa(e) {
    const t = tt
      , {showAlert: n, showConfirm: a} = Be()
      , [i,r] = $("")
      , [o,x] = $(0)
      , [p,h] = $("")
      , m = te(null)
      , l = te({
        dfuService: null,
        dfuInfoCharacteristic: null,
        dfuCallCharacteristic: null,
        dfuBufferCharacteristic: null,
        dfuInfoData: null,
        pendingResponse: null,
        notificationHandler: null
    }).current
      , s = te(e);
    s.current = e;
    const w = te(r);
    w[t(227)] = r;
    const S = te(x);
    S.current = x;
    const I = te(h);
    I[t(227)] = h;
    const M = T(A => {
        const N = t;
        A !== "" && s.current(N(181) + A),
        w[N(227)](A)
    }
    , [])
      , b = T(A => {
        const N = t
          , k = A.target.value
          , D = new Uint8Array(k.buffer,k[N(242)],k[N(172)]);
        if (l.pendingResponse) {
            const U = l[N(188)];
            l[N(188)] = null,
            U[N(213)](D);
            return
        }
        s[N(227)](D[N(201)] > 0 ? N(211) + D[0][N(248)](16) : N(255), "⇓")
    }
    , [l]);
    !l.notificationHandler && (l[t(223)] = A => b(A));
    const v = T( () => !!l[t(251)], [l])
      , E = T( () => {
        const A = t;
        l[A(190)] = null,
        l[A(193)] = null,
        l[A(251)] = null,
        l[A(253)] = null,
        l.dfuInfoData = null,
        l[A(188)] = null,
        w[A(227)](""),
        S[A(227)](0),
        I[A(227)]("")
    }
    , [l])
      , f = T(async (A, N=[], k=!0, D=dn) => {
        const U = t;
        if (!l[U(251)])
            throw new Error(U(210));
        const re = new Uint8Array([A, 0, ...N]);
        if (!k)
            return await l[U(251)][U(180)](re),
            null;
        if (l[U(188)])
            throw new Error(U(221));
        const P = new Promise( (O, _e) => {
            const B = U
              , K = setTimeout( () => {
                const V = Je;
                l.pendingResponse && l.pendingResponse[V(237)] === _e && (l[V(188)] = null),
                _e(new Error(V(239)))
            }
            , D);
            l[B(188)] = {
                resolve: V => {
                    clearTimeout(K),
                    O(V)
                }
                ,
                reject: V => {
                    clearTimeout(K),
                    _e(V)
                }
            }
        }
        );
        return await l[U(251)].writeValueWithResponse(re),
        await P
    }
    , [l])
      , _ = T(async () => {
        const A = t;
        if (!l.dfuInfoCharacteristic)
            return null;
        const N = await l[A(193)][A(218)]()
          , k = new Uint8Array(N[A(244)],N[A(242)],N[A(172)]);
        if (k.length < 12)
            return null;
        const D = {
            dfuVersion: k[0],
            pageSize: 1 << k[1],
            pageCount: k[2] | k[3] << 8,
            chip: Aa(k.slice(4, 8)),
            appStartPage: k[8] | k[9] << 8,
            appPages: k[10] | k[11] << 8,
            bleMtuSize: k[12] | k[13] << 8
        };
        l[A(262)] = D;
        const U = Math[A(238)](D[A(261)] * D[A(254)] / 1024)
          , re = A(178) + D[A(171)] + " | Chip: " + D[A(264)] + " | Flash: " + U + "KB | MTU: " + D.bleMtuSize;
        return s[A(227)]("DFU Info: " + re),
        I.current(re),
        D
    }
    , [l])
      , y = T(async A => {
        const N = t
          , k = await f(ut[N(263)], Et(A), !0)
          , D = k ? k[0] : 255;
        if (D !== 0)
            throw new Error(N(207) + A + N(214) + D[N(248)](16))
    }
    , [f])
      , F = T(async (A, N, k, D=null) => {
        const U = t;
        if (N[U(201)] !== k)
            throw new Error(U(234));
        if (l[U(253)]) {
            const B = l[U(262)] ? (l[U(262)][U(195)] || 23) - 3 : 20;
            let K = hn;
            for (let V = 0; V < N[U(201)]; V += B) {
                const oe = N[U(204)](V, V + B);
                K > 0 && V + B < N[U(201)] ? (K--,
                await l[U(253)][U(183)](oe)) : (await l[U(253)][U(180)](oe),
                K = hn),
                D && D(V + oe.length)
            }
        } else
            for (let K = 0; K < N.length; K += 16) {
                const V = N[U(204)](K, K + 16);
                await f(ut[U(196)], [0, 0, ...V], !1),
                D && D(K + V[U(201)])
            }
        const re = k / 4
          , P = [...Et(A), ...Et(re)]
          , O = await f(ut[U(184)], P, !0, dn * 2)
          , _e = O ? O[0] : 255;
        if (_e !== 0)
            throw new Error(U(198) + A + U(214) + _e[U(248)](16))
    }
    , [l, f])
      , W = T(async () => {
        try {
            await f(ut.RESET, [], !1)
        } catch {}
    }
    , [f])
      , J = T(async A => {
        const N = t;
        if (!A)
            throw new Error(N(182));
        if (l[N(262)] || await _(),
        !l[N(262)])
            throw new Error(N(232));
        const k = l[N(262)]
          , D = k[N(261)]
          , U = k[N(240)] * D
          , re = new Uint8Array(A);
        if (re.length === 0)
            throw new Error(N(176));
        if (re.length > U)
            throw new Error("Firmware is too large for application area");
        const P = Math[N(225)](re.length / D)
          , O = P * D
          , _e = new Uint8Array(O);
        _e[N(185)](255),
        _e[N(192)](re, 0),
        M(N(246)),
        S[N(227)](0),
        await y(k[N(215)]);
        for (let K = 1; K < P; K++) {
            const V = k.appStartPage + K
              , oe = _e[N(204)](K * D, (K + 1) * D);
            await y(V),
            await F(V, oe, D, Ee => {
                const ue = N
                  , ve = ((K - 1) * D + Ee) / (P * D) * 100;
                S.current(ve),
                M(ue(216) + ve[ue(258)](2) + ue(252))
            }
            )
        }
        const B = _e.slice(0, D);
        await F(k.appStartPage, B, D, K => {
            const V = N
              , oe = ((P - 1) * D + K) / (P * D) * 100;
            S[V(227)](oe),
            M(V(216) + oe[V(258)](2) + V(252))
        }
        ),
        W(),
        M(N(199)),
        await n(N(209))
    }
    , [l, _, y, F, W, M, n])
      , le = T(async () => {
        const A = t
          , N = m[A(227)];
        if (!N || N[A(189)][A(201)] === 0) {
            await n("请选择固件文件（.bin）。", "提示");
            return
        }
        if (await a("即将升级固件，升级期间请不要做任何操作，如果升级失败可多重试几次。是否继续？", "DFU 升级确认"))
            try {
                const k = await N[A(189)][0][A(219)]();
                await J(k)
            } catch (k) {
                console[A(212)](k);
                const D = A(249) + (k[A(259)] || k);
                M(D),
                await n(D, "提示")
            }
    }
    , [J, M, n, a])
      , pe = T(async A => {
        const N = t;
        if (E(),
        !A)
            return !1;
        try {
            l[N(190)] = await A[N(186)](Qe[N(175)])
        } catch {
            return !1
        }
        try {
            l[N(193)] = await l.dfuService[N(173)](Qe[N(200)]),
            s[N(227)]("DFU: 找到 info Characteristic"),
            l[N(251)] = await l[N(190)][N(173)](Qe[N(256)]),
            s[N(227)](N(224));
            try {
                l[N(253)] = await l[N(190)][N(173)](Qe[N(194)]),
                s[N(227)]("DFU: 找到 buffer Characteristic")
            } catch {
                l[N(253)] = null
            }
            return await l[N(251)][N(228)](),
            l[N(251)][N(233)](N(247), l.notificationHandler),
            await _(),
            !0
        } catch {
            return E(),
            !1
        }
    }
    , [l, E, _]);
    return {
        dfuStatus: i,
        dfuProgress: o,
        dfuInfo: p,
        dfuFileRef: m,
        isAvailable: v,
        reset: E,
        attachServer: pe,
        start: le,
        resetChip: W
    }
}
const Vn = In(null)
  , be = {
    SET_PINS: 0,
    INIT: 1,
    CLEAR: 2,
    SEND_CMD: 3,
    SEND_DATA: 4,
    REFRESH: 5,
    SLEEP: 6,
    SET_TIME: 32,
    SET_COUNTDOWN: 34,
    SET_HOLIDAYS: 35,
    WRITE_IMG: 48,
    SET_SLOT: 49,
    FREE_SLOT: 50,
    SET_SLIDE: 51,
    SET_CONFIG: 144,
    SYS_RESET: 145,
    SYS_SLEEP: 146,
    CFG_ERASE: 153
};
function jn(e) {
    const t = [];
    for (let n = 0; n < e.length; n += 2)
        t.push(parseInt(e.substr(n, 2), 16));
    return new Uint8Array(t)
}
function et(e) {
    return new Uint8Array(e).reduce( (t, n) => t + ("0" + n.toString(16)).slice(-2), "")
}
function za({children: e}) {
    const [t,n] = $( () => new URLSearchParams(window.location.search).get("debug") === "true")
      , [a,i] = $(!1)
      , [r,o] = $(!1)
      , [x,p] = $(!1)
      , [h,m] = $([])
      , [l,s] = $("01")
      , [w,S] = $("")
      , [I,M] = $("4.2_400_300")
      , [b,v] = $("blackWhiteColor")
      , [E,f] = $("floydSteinberg")
      , [_,y] = $(1)
      , [F,W] = $(1)
      , [J,le] = $(1.2)
      , [pe,A] = $(20)
      , [N,k] = $( () => parseInt(localStorage.getItem("interleavedCount") || "10"))
      , [D,U] = $(!0)
      , [re,P] = $({
        count: 0,
        usedMask: 0
    })
      , [O,_e] = $(-1)
      , [B,K] = $("")
      , [V,oe] = $(!1)
      , [Ee,ue] = $(!1)
      , [ve,d] = $( () => localStorage.getItem("bleNamePrefix") || "")
      , u = T(we => {
        localStorage.setItem("interleavedCount", we),
        k(we)
    }
    , [])
      , C = T(we => {
        localStorage.setItem("bleNamePrefix", we),
        d(we)
    }
    , [])
      , z = te(null)
      , j = te(null)
      , ae = te(null)
      , se = te(!1)
      , X = te(!1)
      , ce = te(0)
      , Z = te(null)
      , ye = te(null)
      , Ce = te(null)
      , xe = te(new TextDecoder)
      , Ie = "未检测到适配固件，请重新连接设备。"
      , Q = T( (we, ke="") => {
        m(Ae => {
            const Me = new Date
              , Fe = String(Me.getHours()).padStart(2, "0") + ":" + String(Me.getMinutes()).padStart(2, "0") + ":" + String(Me.getSeconds()).padStart(2, "0");
            if (Ae.length > 0) {
                const De = Ae[Ae.length - 1];
                if (De.text === we && De.action === ke) {
                    const Ve = [...Ae];
                    return Ve[Ve.length - 1] = {
                        ...De,
                        count: De.count + 1
                    },
                    Ve
                }
            }
            const Te = [...Ae, {
                time: Fe,
                text: we,
                action: ke,
                count: 1,
                id: Date.now() + Math.random()
            }];
            return Te.length > 20 ? Te.slice(-20) : Te
        }
        )
    }
    , [])
      , de = T( () => m([]), [])
      , Se = Pa(Q)
      , Ge = T(async (we, ke, Ae=!0) => {
        const Me = ae.current;
        if (!Me)
            return Q("服务不可用，请检查蓝牙连接", "⚠️"),
            !1;
        if (X.current && !se.current && ![0, 1, 145, 152, 153].includes(we))
            return Q(Ie, "⚠️"),
            z.current?.gatt?.connected && z.current.gatt.disconnect(),
            !1;
        let Fe = [we];
        ke && (typeof ke == "string" && (ke = jn(ke)),
        ke instanceof Uint8Array && (ke = Array.from(ke)),
        Fe.push(...ke)),
        t && Q(et(Fe), "⇑");
        try {
            Ae ? await Me.writeValueWithResponse(Uint8Array.from(Fe)) : await Me.writeValueWithoutResponse(Uint8Array.from(Fe))
        } catch (Te) {
            return console.error(Te),
            Te.message && Q("write: " + Te.message, "⚠️"),
            !1
        }
        return !0
    }
    , [Q, t])
      , ot = T( () => z.current != null && z.current.gatt.connected, [])
      , ct = {
        debugMode: t,
        setDebugMode: n,
        connected: a,
        setConnected: i,
        dfuMode: r,
        setDfuMode: o,
        dfuAvailable: x,
        setDfuAvailable: p,
        logs: h,
        addLog: Q,
        clearLog: de,
        epdDriver: l,
        setEpdDriver: s,
        epdPins: w,
        setEpdPins: S,
        canvasSize: I,
        setCanvasSize: M,
        ditherMode: b,
        setDitherMode: v,
        ditherAlg: E,
        setDitherAlg: f,
        ditherStrength: _,
        setDitherStrength: y,
        ditherBrightness: F,
        setDitherBrightness: W,
        ditherContrast: J,
        setDitherContrast: le,
        mtuSize: pe,
        setMtuSize: A,
        interleavedCount: N,
        setInterleavedCount: u,
        clockEnable: D,
        setClockEnable: U,
        slots: re,
        setSlots: P,
        selectedSlot: O,
        setSelectedSlot: _e,
        statusText: B,
        setStatusText: K,
        showStatus: V,
        setShowStatus: oe,
        sending: Ee,
        setSending: ue,
        bleNamePrefix: ve,
        setBleNamePrefix: C,
        bleDeviceRef: z,
        gattServerRef: j,
        epdCharRef: ae,
        sidValidRef: se,
        checkSidRef: X,
        msgIndexRef: ce,
        canvasRef: Z,
        ctxRef: ye,
        sidRef: Ce,
        textDecoderRef: xe,
        write: Ge,
        isConnected: ot,
        unsupportedMsg: Ie,
        dfu: Se
    };
    return c(Vn.Provider, {
        value: ct,
        children: e
    })
}
function Le() {
    return Pn(Vn)
}
const Xn = (...e) => e.filter( (t, n, a) => !!t && t.trim() !== "" && a.indexOf(t) === n).join(" ").trim();
const Ua = e => e.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
const La = e => e.replace(/^([A-Z])|[\s-_]+(\w)/g, (t, n, a) => a ? a.toUpperCase() : n.toLowerCase());
const fn = e => {
    const t = La(e);
    return t.charAt(0).toUpperCase() + t.slice(1)
}
;
var Fa = {
    xmlns: "http://www.w3.org/2000/svg",
    width: 24,
    height: 24,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round",
    strokeLinejoin: "round"
};
const Wa = e => {
    for (const t in e)
        if (t.startsWith("aria-") || t === "role" || t === "title")
            return !0;
    return !1
}
;
const $a = Fn( ({color: e="currentColor", size: t=24, strokeWidth: n=2, absoluteStrokeWidth: a, className: i="", children: r, iconNode: o, ...x}, p) => je("svg", {
    ref: p,
    ...Fa,
    width: t,
    height: t,
    stroke: e,
    strokeWidth: a ? Number(n) * 24 / Number(t) : n,
    className: Xn("lucide", i),
    ...!r && !Wa(x) && {
        "aria-hidden": "true"
    },
    ...x
}, [...o.map( ([h,m]) => je(h, m)), ...Array.isArray(r) ? r : [r]]));
const ie = (e, t) => {
    const n = Fn( ({className: a, ...i}, r) => je($a, {
        ref: r,
        iconNode: t,
        className: Xn(`lucide-${Ua(fn(e))}`, `lucide-${e}`, a),
        ...i
    }));
    return n.displayName = fn(e),
    n
}
;
const Oa = [["path", {
    d: "M12 5v14",
    key: "s699le"
}], ["path", {
    d: "m19 12-7 7-7-7",
    key: "1idqje"
}]]
  , Ha = ie("arrow-down", Oa);
const Ba = [["path", {
    d: "m12 19-7-7 7-7",
    key: "1l729n"
}], ["path", {
    d: "M19 12H5",
    key: "x3x0zl"
}]]
  , Va = ie("arrow-left", Ba);
const ja = [["path", {
    d: "M5 12h14",
    key: "1ays0h"
}], ["path", {
    d: "m12 5 7 7-7 7",
    key: "xquz4c"
}]]
  , Xa = ie("arrow-right", ja);
const Ya = [["path", {
    d: "m5 12 7-7 7 7",
    key: "hav0vg"
}], ["path", {
    d: "M12 19V5",
    key: "x0mq9r"
}]]
  , Ja = ie("arrow-up", Ya);
const qa = [["path", {
    d: "m7 7 10 10-5 5V2l5 5L7 17",
    key: "1q5490"
}]]
  , Ga = ie("bluetooth", qa);
const Ka = [["path", {
    d: "M6 12h9a4 4 0 0 1 0 8H7a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h7a4 4 0 0 1 0 8",
    key: "mg9rjx"
}]]
  , Za = ie("bold", Ka);
const Qa = [["path", {
    d: "M8 2v4",
    key: "1cmpym"
}], ["path", {
    d: "M16 2v4",
    key: "4m81vk"
}], ["rect", {
    width: "18",
    height: "18",
    x: "3",
    y: "4",
    rx: "2",
    key: "1hopcy"
}], ["path", {
    d: "M3 10h18",
    key: "8toen8"
}], ["path", {
    d: "M8 14h.01",
    key: "6423bh"
}], ["path", {
    d: "M12 14h.01",
    key: "1etili"
}], ["path", {
    d: "M16 14h.01",
    key: "1gbofw"
}], ["path", {
    d: "M8 18h.01",
    key: "lrp35t"
}], ["path", {
    d: "M12 18h.01",
    key: "mhygvu"
}], ["path", {
    d: "M16 18h.01",
    key: "kzsmim"
}]]
  , er = ie("calendar-days", Qa);
const tr = [["path", {
    d: "M13.997 4a2 2 0 0 1 1.76 1.05l.486.9A2 2 0 0 0 18.003 7H20a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h1.997a2 2 0 0 0 1.759-1.048l.489-.904A2 2 0 0 1 10.004 4z",
    key: "18u6gg"
}], ["circle", {
    cx: "12",
    cy: "13",
    r: "3",
    key: "1vg3eu"
}]]
  , nr = ie("camera", tr);
const ar = [["path", {
    d: "M21 21H8a2 2 0 0 1-1.42-.587l-3.994-3.999a2 2 0 0 1 0-2.828l10-10a2 2 0 0 1 2.829 0l5.999 6a2 2 0 0 1 0 2.828L12.834 21",
    key: "g5wo59"
}], ["path", {
    d: "m5.082 11.09 8.828 8.828",
    key: "1wx5vj"
}]]
  , rr = ie("eraser", ar);
const or = [["path", {
    d: "M10.3 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10l-3.1-3.1a2 2 0 0 0-2.814.014L6 21",
    key: "9csbqa"
}], ["path", {
    d: "m14 19.5 3-3 3 3",
    key: "9vmjn0"
}], ["path", {
    d: "M17 22v-5.5",
    key: "1aa6fl"
}], ["circle", {
    cx: "9",
    cy: "9",
    r: "2",
    key: "af1f0g"
}]]
  , cr = ie("image-up", or);
const ir = [["rect", {
    width: "18",
    height: "18",
    x: "3",
    y: "3",
    rx: "2",
    ry: "2",
    key: "1m3agn"
}], ["circle", {
    cx: "9",
    cy: "9",
    r: "2",
    key: "af1f0g"
}], ["path", {
    d: "m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21",
    key: "1xmnt7"
}]]
  , lr = ie("image", ir);
const sr = [["line", {
    x1: "19",
    x2: "10",
    y1: "4",
    y2: "4",
    key: "15jd3p"
}], ["line", {
    x1: "14",
    x2: "5",
    y1: "20",
    y2: "20",
    key: "bu0au3"
}], ["line", {
    x1: "15",
    x2: "9",
    y1: "4",
    y2: "20",
    key: "uljnxc"
}]]
  , xr = ie("italic", sr);
const ur = [["path", {
    d: "M18 8V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h8",
    key: "10dyio"
}], ["path", {
    d: "M10 19v-3.96 3.15",
    key: "1irgej"
}], ["path", {
    d: "M7 19h5",
    key: "qswx4l"
}], ["rect", {
    width: "6",
    height: "10",
    x: "16",
    y: "12",
    rx: "2",
    key: "1egngj"
}]]
  , dr = ie("monitor-smartphone", ur);
const hr = [["path", {
    d: "M20.985 12.486a9 9 0 1 1-9.473-9.472c.405-.022.617.46.402.803a6 6 0 0 0 8.268 8.268c.344-.215.825-.004.803.401",
    key: "kfwtm"
}]]
  , fr = ie("moon", hr);
const _r = [["path", {
    d: "M12 22a1 1 0 0 1 0-20 10 9 0 0 1 10 9 5 5 0 0 1-5 5h-2.25a1.75 1.75 0 0 0-1.4 2.8l.3.4a1.75 1.75 0 0 1-1.4 2.8z",
    key: "e79jfc"
}], ["circle", {
    cx: "13.5",
    cy: "6.5",
    r: ".5",
    fill: "currentColor",
    key: "1okk4w"
}], ["circle", {
    cx: "17.5",
    cy: "10.5",
    r: ".5",
    fill: "currentColor",
    key: "f64h9f"
}], ["circle", {
    cx: "6.5",
    cy: "12.5",
    r: ".5",
    fill: "currentColor",
    key: "qy21gx"
}], ["circle", {
    cx: "8.5",
    cy: "7.5",
    r: ".5",
    fill: "currentColor",
    key: "fotxhn"
}]]
  , pr = ie("palette", _r);
const mr = [["path", {
    d: "M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z",
    key: "1a8usu"
}], ["path", {
    d: "m15 5 4 4",
    key: "1mk7zo"
}]]
  , br = ie("pencil", mr);
const gr = [["path", {
    d: "m15 14 5-5-5-5",
    key: "12vg1m"
}], ["path", {
    d: "M20 9H9.5A5.5 5.5 0 0 0 4 14.5A5.5 5.5 0 0 0 9.5 20H13",
    key: "6uklza"
}]]
  , vr = ie("redo-2", gr);
const yr = [["path", {
    d: "M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8",
    key: "1357e3"
}], ["path", {
    d: "M3 3v5h5",
    key: "1xhq8a"
}]]
  , wr = ie("rotate-ccw", yr);
const Cr = [["path", {
    d: "M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8",
    key: "1p45f6"
}], ["path", {
    d: "M21 3v5h-5",
    key: "1q7to0"
}]]
  , kr = ie("rotate-cw", Cr);
const Sr = [["path", {
    d: "M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915",
    key: "1i5ecw"
}], ["circle", {
    cx: "12",
    cy: "12",
    r: "3",
    key: "1v7zrd"
}]]
  , Nr = ie("settings", Sr);
const Mr = [["path", {
    d: "M5 3a2 2 0 0 0-2 2",
    key: "y57alp"
}], ["path", {
    d: "M19 3a2 2 0 0 1 2 2",
    key: "18rm91"
}], ["path", {
    d: "M21 19a2 2 0 0 1-2 2",
    key: "1j7049"
}], ["path", {
    d: "M5 21a2 2 0 0 1-2-2",
    key: "sbafld"
}], ["path", {
    d: "M9 3h1",
    key: "1yesri"
}], ["path", {
    d: "M9 21h1",
    key: "15o7lz"
}], ["path", {
    d: "M14 3h1",
    key: "1ec4yj"
}], ["path", {
    d: "M14 21h1",
    key: "v9vybs"
}], ["path", {
    d: "M3 9v1",
    key: "1r0deq"
}], ["path", {
    d: "M21 9v1",
    key: "mxsmne"
}], ["path", {
    d: "M3 14v1",
    key: "vnatye"
}], ["path", {
    d: "M21 14v1",
    key: "169vum"
}]]
  , Tr = ie("square-dashed", Mr);
const Dr = [["circle", {
    cx: "12",
    cy: "12",
    r: "4",
    key: "4exip2"
}], ["path", {
    d: "M12 2v2",
    key: "tus03m"
}], ["path", {
    d: "M12 20v2",
    key: "1lh1kg"
}], ["path", {
    d: "m4.93 4.93 1.41 1.41",
    key: "149t6j"
}], ["path", {
    d: "m17.66 17.66 1.41 1.41",
    key: "ptbguv"
}], ["path", {
    d: "M2 12h2",
    key: "1t8f8n"
}], ["path", {
    d: "M20 12h2",
    key: "1q8mjw"
}], ["path", {
    d: "m6.34 17.66-1.41 1.41",
    key: "1m8zz5"
}], ["path", {
    d: "m19.07 4.93-1.41 1.41",
    key: "1shlcs"
}]]
  , Er = ie("sun", Dr);
const Ir = [["line", {
    x1: "10",
    x2: "14",
    y1: "2",
    y2: "2",
    key: "14vaq8"
}], ["line", {
    x1: "12",
    x2: "15",
    y1: "14",
    y2: "11",
    key: "17fdiu"
}], ["circle", {
    cx: "12",
    cy: "14",
    r: "8",
    key: "1e1u0o"
}]]
  , Rr = ie("timer", Ir);
const Ar = [["path", {
    d: "M12 4v16",
    key: "1654pz"
}], ["path", {
    d: "M4 7V5a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v2",
    key: "e0r10z"
}], ["path", {
    d: "M9 20h6",
    key: "s66wpe"
}]]
  , Pr = ie("type", Ar);
const zr = [["path", {
    d: "M9 14 4 9l5-5",
    key: "102s5s"
}], ["path", {
    d: "M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11",
    key: "f3b9sd"
}]]
  , Ur = ie("undo-2", zr);
const Lr = [["path", {
    d: "M18 6 6 18",
    key: "1bl5f8"
}], ["path", {
    d: "m6 6 12 12",
    key: "d8bk6v"
}]]
  , Fr = ie("x", Lr);
const Wr = [["circle", {
    cx: "11",
    cy: "11",
    r: "8",
    key: "4ej97u"
}], ["line", {
    x1: "21",
    x2: "16.65",
    y1: "21",
    y2: "16.65",
    key: "13gj7c"
}], ["line", {
    x1: "11",
    x2: "11",
    y1: "8",
    y2: "14",
    key: "1vmskp"
}], ["line", {
    x1: "8",
    x2: "14",
    y1: "11",
    y2: "11",
    key: "durymu"
}]]
  , $r = ie("zoom-in", Wr);
const Or = [["circle", {
    cx: "11",
    cy: "11",
    r: "8",
    key: "4ej97u"
}], ["line", {
    x1: "21",
    x2: "16.65",
    y1: "21",
    y2: "16.65",
    key: "13gj7c"
}], ["line", {
    x1: "8",
    x2: "14",
    y1: "11",
    y2: "11",
    key: "durymu"
}]]
  , Hr = ie("zoom-out", Or);
function Br({onSettingsClick: e}) {
    const {debugMode: t, dfuMode: n, connected: a, bleDeviceRef: i} = Le();
    return c("header", {
        className: "app-header",
        children: [c("div", {
            className: "header-brand",
            children: [c(er, {
                size: 18
            }), c("span", {
                children: n ? "DFU 模式" : "墨水屏日历"
            }), t && c("span", {
                className: "header-mode-badge",
                children: "DEV"
            })]
        }), c("div", {
            className: "header-status",
            children: [c("div", {
                className: `status-dot ${a ? "connected" : ""}`
            }), c("span", {
                children: a ? i.current?.name || "已连接" : "未连接"
            }), c("button", {
                className: "settings-toggle",
                onClick: e,
                title: "设置",
                children: c(Nr, {
                    size: 15
                })
            })]
        })]
    })
}
function Vr() {
    const {logs: e} = Le()
      , t = te(null);
    return Ue( () => {
        t.current && (t.current.scrollTop = t.current.scrollHeight)
    }
    , [e]),
    c("div", {
        className: "log-container",
        ref: t,
        children: e.map(n => c("div", {
            className: "log-line",
            children: [c("span", {
                className: "time",
                children: [n.time, " "]
            }), n.action && c("span", {
                className: "action",
                children: [n.action, " "]
            }), c("span", {
                className: "log-text",
                children: n.text
            }), n.count > 1 && c("span", {
                className: "dup-count",
                children: [" (x", n.count, ")"]
            })]
        }, n.id))
    })
}
const _n = [{
    value: "13",
    color: "fourColor",
    size: "3.98_768_552",
    label: "3.98寸A0 (四色, JD79665)"
}, {
    value: "14",
    color: "fourColor",
    size: "3.98_768_552",
    label: "3.98寸A1 (四色, JD79665)"
}, {
    value: "01",
    color: "blackWhiteColor",
    size: "4.2_400_300",
    label: "4.2寸 (黑白, UC8176)"
}, {
    value: "03",
    color: "threeColor",
    size: "4.2_400_300",
    label: "4.2寸 (三色, UC8176)"
}, {
    value: "04",
    color: "blackWhiteColor",
    size: "4.2_400_300",
    label: "4.2寸 (黑白, SSD1619)"
}, {
    value: "02",
    color: "threeColor",
    size: "4.2_400_300",
    label: "4.2寸 (三色, SSD1619)"
}, {
    value: "17",
    color: "blackWhiteColor",
    size: "4.2_400_300",
    label: "4.2寸 (黑白, SSD1683)"
}, {
    value: "16",
    color: "threeColor",
    size: "4.2_400_300",
    label: "4.2寸 (三色, SSD1683)"
}, {
    value: "05",
    color: "fourColor",
    size: "4.2_400_300",
    label: "4.2寸 (四色, JD79668)"
}, {
    value: "19",
    color: "blackWhiteColor",
    size: "5.83_648_480",
    label: "5.83寸 (黑白, UC8179)"
}, {
    value: "18",
    color: "threeColor",
    size: "5.83_648_480",
    label: "5.83寸 (三色, UC8179)"
}, {
    value: "0f",
    color: "blackWhiteColor",
    size: "5.83_648_480",
    label: "5.83寸 (黑白, JD79686)"
}, {
    value: "0e",
    color: "threeColor",
    size: "5.83_648_480",
    label: "5.83寸 (三色, JD79686)"
}, {
    value: "0d",
    color: "fourColor",
    size: "5.83_648_480",
    label: "5.83寸 (四色, JD79665)"
}, {
    value: "06",
    color: "blackWhiteColor",
    size: "7.5_800_480",
    label: "7.5寸 (黑白, UC8179)"
}, {
    value: "07",
    color: "threeColor",
    size: "7.5_800_480",
    label: "7.5寸 (三色, UC8179)"
}, {
    value: "0c",
    color: "fourColor",
    size: "7.5_800_480",
    label: "7.5寸 (四色, JD79665)"
}, {
    value: "08",
    color: "blackWhiteColor",
    size: "7.5_640_384",
    label: "7.5寸低分 (黑白, UC8159)"
}, {
    value: "09",
    color: "threeColor",
    size: "7.5_640_384",
    label: "7.5寸低分 (三色, UC8159)"
}, {
    value: "0a",
    color: "blackWhiteColor",
    size: "7.5_880_528",
    label: "7.5寸HD (黑白, SSD1677)"
}, {
    value: "0b",
    color: "threeColor",
    size: "7.5_880_528",
    label: "7.5寸HD (三色, SSD1677)"
}, {
    value: "11",
    color: "threeColor",
    size: "10.2_960_640",
    label: "10.2寸 (三色, SSD1677)"
}, {
    value: "12",
    color: "blackWhiteColor",
    size: "10.2_960_640",
    label: "10.2寸 (黑白, SSD1677)"
}, {
    value: "10",
    color: "fourColor",
    size: "10.2_960_640",
    label: "10.2寸 (四色, SSD2677)"
}, {
    value: "15",
    color: "sixColor",
    size: "7.3E6_800_480",
    label: "7.3寸 (六色, Spectra 6)"
}]
  , pn = [{
    value: "33",
    color: "blackWhiteColor",
    size: "2.13_250_122",
    label: "2.13寸 (黑白, SSD1675)"
}, {
    value: "32",
    color: "threeColor",
    size: "2.13_250_122",
    label: "2.13寸 (三色, SSD1675)"
}, {
    value: "35",
    color: "blackWhiteColor",
    size: "2.13_212_104",
    label: "2.13寸低分 (黑白, SSD1675)"
}, {
    value: "34",
    color: "threeColor",
    size: "2.13_212_104",
    label: "2.13寸低分 (三色, SSD1675)"
}, {
    value: "3b",
    color: "blackWhiteColor",
    size: "2.13_250_122",
    label: "2.13寸 (黑白, SSD1680)"
}, {
    value: "3a",
    color: "threeColor",
    size: "2.13_250_122",
    label: "2.13寸 (三色, SSD1680)"
}, {
    value: "48",
    color: "blackWhiteColor",
    size: "2.13_212_104",
    label: "2.13寸低分 (黑白, SSD1680)"
}, {
    value: "47",
    color: "threeColor",
    size: "2.13_212_104",
    label: "2.13寸低分 (三色, SSD1680)"
}, {
    value: "4d",
    color: "blackWhiteColor",
    size: "2.13_250_122",
    label: "2.13寸 (黑白, SSD1608)"
}, {
    value: "37",
    color: "blackWhiteColor",
    size: "2.13_250_122",
    label: "2.13寸 (黑白, UC8151)"
}, {
    value: "36",
    color: "threeColor",
    size: "2.13_250_122",
    label: "2.13寸 (三色, UC8151)"
}, {
    value: "39",
    color: "blackWhiteColor",
    size: "2.13_212_104",
    label: "2.13寸低分 (黑白, UC8151)"
}, {
    value: "38",
    color: "threeColor",
    size: "2.13_212_104",
    label: "2.13寸低分 (三色, UC8151)"
}, {
    value: "4c",
    color: "blackWhiteColor",
    size: "2.13_250_122",
    label: "2.13寸 (黑白, JD79651)"
}, {
    value: "4b",
    color: "threeColor",
    size: "2.13_250_122",
    label: "2.13寸 (三色, JD79651)"
}, {
    value: "4a",
    color: "blackWhiteColor",
    size: "2.66_296_152",
    label: "2.6寸 (黑白, SSD1675)"
}, {
    value: "49",
    color: "threeColor",
    size: "2.66_296_152",
    label: "2.6寸 (三色, SSD1675)"
}, {
    value: "3d",
    color: "blackWhiteColor",
    size: "2.66_296_152",
    label: "2.6寸 (黑白, SSD1680)"
}, {
    value: "3c",
    color: "threeColor",
    size: "2.66_296_152",
    label: "2.6寸 (三色, SSD1680)"
}, {
    value: "3f",
    color: "blackWhiteColor",
    size: "2.66_296_152",
    label: "2.6寸 (黑白, UC8151)"
}, {
    value: "3e",
    color: "threeColor",
    size: "2.66_296_152",
    label: "2.6寸 (三色, UC8151)"
}, {
    value: "45",
    color: "blackWhiteColor",
    size: "2.9_296_128",
    label: "2.9寸 (黑白, SSD1675)"
}, {
    value: "44",
    color: "threeColor",
    size: "2.9_296_128",
    label: "2.9寸 (三色, SSD1675)"
}, {
    value: "41",
    color: "blackWhiteColor",
    size: "2.9_296_128",
    label: "2.9寸 (黑白, SSD1680)"
}, {
    value: "40",
    color: "threeColor",
    size: "2.9_296_128",
    label: "2.9寸 (三色, SSD1680)"
}, {
    value: "43",
    color: "blackWhiteColor",
    size: "2.9_296_128",
    label: "2.9寸 (黑白, UC8151)"
}, {
    value: "42",
    color: "threeColor",
    size: "2.9_296_128",
    label: "2.9寸 (三色, UC8151)"
}, {
    value: "46",
    color: "blackWhiteColor",
    size: "2.9_296_128",
    label: "2.9寸 (黑白, SSD1608)"
}];
function jr() {
    const {debugMode: e, connected: t, dfuMode: n, epdDriver: a, setEpdDriver: i, epdPins: r, setEpdPins: o, addLog: x, clearLog: p, write: h, bleDeviceRef: m, gattServerRef: l, epdCharRef: s, sidValidRef: w, checkSidRef: S, msgIndexRef: I, setConnected: M, setDfuMode: b, setDfuAvailable: v, setMtuSize: E, setClockEnable: f, slots: _, setSlots: y, setSelectedSlot: F, textDecoderRef: W, sidRef: J, dfu: le, isConnected: pe, unsupportedMsg: A, bleNamePrefix: N, setDitherMode: k, setCanvasSize: D, sending: U} = Le()
      , {showAlert: re, showConfirm: P} = Be()
      , [O,_e] = $(!1)
      , B = te(!1)
      , K = te(null)
      , V = te(0)
      , oe = te(0)
      , Ee = te(!1)
      , ue = T(X => {
        const ce = (B.current ? pn : _n).find(Z => Z.value === X);
        ce && (ce.color && k(ce.color),
        ce.size && D(ce.size))
    }
    , [k, D])
      , ve = T( () => {
        l.current = null,
        s.current = null,
        I.current = 0,
        w.current = !1,
        S.current = !1,
        F(-1),
        y({
            count: 0,
            usedMask: 0
        }),
        v(!1),
        K.current = null,
        V.current = 0,
        le.reset()
    }
    , [l, s, I, w, S, le, v])
      , d = T( () => {
        M(!1),
        ve(),
        x("已断开连接.")
    }
    , [M, ve, x])
      , u = T(async X => {
        let ce = A;
        try {
            const Z = new URLSearchParams;
            Z.append("hash", X);
            const ye = await fetch("/ecc/check", {
                method: "POST",
                body: Z,
                signal: AbortSignal.timeout(3e3)
            });
            if (ye.ok) {
                const Ce = await ye.text();
                w.current = Ce === "OK"
            }
        } catch (Z) {
            Z.name === "TimeoutError" && (ce = "网络请求超时，请检查网络连接。"),
            console.error(Z)
        }
        w.current || (x(ce, "⚠️"),
        await re(ce, "错误"),
        pe() && m.current.gatt.disconnect())
    }
    , [x, w, pe, m, A])
      , C = T(async (X, ce) => {
        const Z = new Uint8Array(X.buffer,X.byteOffset,X.byteLength)
          , ye = async (xe, Ie) => {
            if (Ie) {
                e && x(`收到配置：${et(xe)}`);
                let Q = et(xe.slice(0, 7));
                xe.length > 10 && (Q += et(xe.slice(10, 11))),
                o(Q);
                const de = et(xe.slice(7, 8));
                i(de),
                xe.length > 13 && F(xe[13]),
                ue(de)
            } else {
                const Q = W.current.decode(xe);
                if (Q.startsWith("mtu=") && Q.length > 4) {
                    const de = parseInt(Q.substring(4));
                    E(de),
                    e && x(`MTU 已更新为: ${de}`)
                } else if (Q.startsWith("t=") && Q.length > 2) {
                    if (e) {
                        const de = parseInt(Q.substring(2)) + new Date().getTimezoneOffset() * 60;
                        x(`远端时间: ${new Date(de * 1e3).toLocaleString()}`),
                        x(`本地时间: ${new Date().toLocaleString()}`)
                    }
                } else if (Q.startsWith("sid=") && Q.length > 4) {
                    const de = Q.substring(4);
                    J.current = de,
                    await u(de)
                } else if (Q.startsWith("clock_enable=") && Q.length > 13) {
                    const de = Q.substring(13) === "1";
                    f(de),
                    de || x("提醒：此固件版本不支持时钟模式，已切换为刷新模式按钮。", "⚠️")
                } else if (Q.startsWith("nrf_dfu=") && Q.length > 8)
                    v(Q.substring(8) === "1");
                else if (Q.startsWith("slots=") && Q.length > 6) {
                    const de = Q.substring(6).split(" ")
                      , Se = parseInt(de[0])
                      , Ge = de.length > 1 ? parseInt(de[1]) : 0;
                    y({
                        count: Se,
                        usedMask: Ge
                    }),
                    de.length > 2 && F(parseInt(de[2]))
                } else
                    e && x(Q, "⇓")
            }
        }
        ;
        if (K.current !== null) {
            const xe = Math.min(Z.length, oe.current - V.current);
            if (K.current.set(Z.slice(0, xe), V.current),
            V.current += xe,
            V.current >= oe.current) {
                const Ie = K.current
                  , Q = Ee.current;
                K.current = null,
                V.current = 0,
                await ye(Ie, Q)
            }
            return
        }
        const Ce = W.current.decode(Z.slice(0, Math.min(Z.length, 20)));
        if (Ce.startsWith("chunk=")) {
            const xe = Ce.match(/^chunk=(\d+) len=(\d+)/);
            if (xe) {
                oe.current = parseInt(xe[2]),
                K.current = new Uint8Array(oe.current),
                V.current = 0,
                Ee.current = ce === 0;
                return
            }
        }
        await ye(Z, ce === 0)
    }
    , [e, x, o, i, E, f, v, _, W, J, u, ue])
      , z = T(async () => {
        const X = m.current;
        if (!(X == null || s.current != null))
            try {
                if (x("正在连接: " + X.name),
                l.current = await X.gatt.connect(),
                x("  找到 GATT Server"),
                M(!0),
                e) {
                    const Z = await le.attachServer(l.current) && le.isAvailable();
                    if (b(Z),
                    Z) {
                        await P("检测到处于 DFU 模式的设备，是否继续固件升级？") && await le.start();
                        return
                    }
                }
                const ce = await l.current.getPrimaryService("62750001-d828-918d-fb46-b6c11c675aec");
                x("  找到 EPD Service"),
                s.current = await ce.getCharacteristic("62750002-d828-918d-fb46-b6c11c675aec"),
                x("  找到 Characteristic");
                try {
                    const ye = await (await ce.getCharacteristic("62750003-d828-918d-fb46-b6c11c675aec")).readValue();
                    if (ye.byteLength > 1) {
                        const Ce = new Uint8Array(ye.buffer,ye.byteOffset,ye.byteLength)
                          , xe = W.current.decode(Ce).replace(/\0+$/, "");
                        x(`固件版本: ${xe}`),
                        B.current = xe.endsWith("-s"),
                        _e(B.current)
                    } else {
                        const Ce = ye.getUint8(0);
                        x(`固件版本: 0x${Ce.toString(16)}`)
                    }
                } catch (Z) {
                    console.error(Z)
                }
                f(!0);
                try {
                    await s.current.startNotifications(),
                    s.current.addEventListener("characteristicvaluechanged", Z => {
                        C(Z.target.value, I.current++)
                    }
                    )
                } catch (Z) {
                    console.error(Z),
                    Z.message && x("startNotifications: " + Z.message, "⚠️")
                }
                setTimeout( () => {
                    S.current = !0
                }
                , 5e3),
                await h(be.INIT)
            } catch (ce) {
                console.error(ce),
                ce.message && x("connect: " + ce.message, "⚠️"),
                d()
            }
    }
    , [x, m, l, s, le, e, I, S, W, M, b, f, h, d, C])
      , j = T(async () => {
        if (l.current != null && l.current.connected)
            pe() && m.current.gatt.disconnect();
        else {
            ve(),
            p();
            try {
                const X = ["62750001-d828-918d-fb46-b6c11c675aec", Qe.SERVICE];
                m.current = await navigator.bluetooth.requestDevice(N ? {
                    filters: [{
                        namePrefix: N
                    }],
                    optionalServices: X
                } : {
                    optionalServices: X,
                    acceptAllDevices: !0
                })
            } catch (X) {
                console.error(X),
                X.message && x("requestDevice: " + X.message, "⚠️"),
                x("请检查蓝牙是否已开启，且使用的浏览器支持蓝牙！建议使用以下浏览器："),
                x("• 电脑: Chrome/Edge"),
                x("• Android: Chrome/Edge"),
                x("• iOS: Bluefy 浏览器");
                return
            }
            m.current.addEventListener("gattserverdisconnected", d),
            setTimeout( () => z(), 300)
        }
    }
    , [l, m, pe, ve, p, x, d, z, N])
      , ae = T(async () => {
        pe() && m.current.gatt.disconnect(),
        ve(),
        p(),
        x("正在重连"),
        setTimeout( () => z(), 300)
    }
    , [pe, m, ve, p, x, z])
      , se = T(async () => {
        _.count > 0 && !await P("切换驱动可能会导致图片槽位重新分配（已上传的图片也会无法访问），是否继续？", "警告") || (await h(be.SET_PINS, r),
        setTimeout( () => h(be.INIT, a), 500))
    }
    , [_.count, h, r, a]);
    return c("div", {
        className: "card",
        children: [c("div", {
            className: "card-header",
            children: [c(Ga, {
                size: 15
            }), "蓝牙连接"]
        }), c("div", {
            className: "card-body",
            children: c("div", {
                className: "flex-container",
                children: [c("div", {
                    className: "flex-group",
                    children: [c("button", {
                        type: "button",
                        className: "primary",
                        onClick: j,
                        children: t ? "断开" : "连接"
                    }), c("button", {
                        type: "button",
                        onClick: ae,
                        disabled: !m.current || t,
                        children: "重连"
                    }), c("button", {
                        type: "button",
                        onClick: p,
                        children: "清空日志"
                    })]
                }), e && !n && c("div", {
                    className: "flex-group right",
                    children: [c("label", {
                        children: "驱动"
                    }), c("select", {
                        value: a,
                        onChange: X => {
                            i(X.target.value),
                            ue(X.target.value)
                        }
                        ,
                        children: (O ? pn : _n).map(X => c("option", {
                            value: X.value,
                            children: X.label
                        }, X.value))
                    })]
                }), e && !n && c("div", {
                    className: "flex-group",
                    children: [c("label", {
                        children: "引脚"
                    }), c("input", {
                        type: "text",
                        value: r,
                        onChange: X => o(X.target.value)
                    }), c("button", {
                        type: "button",
                        className: "primary",
                        onClick: se,
                        disabled: !t || U,
                        children: "确定"
                    })]
                })]
            })
        }), c(Vr, {})]
    })
}
function Xr() {
    const {debugMode: e, connected: t, sending: n, write: a, addLog: i, mtuSize: r, clockEnable: o, slots: x, selectedSlot: p, setSelectedSlot: h, sidRef: m} = Le()
      , {showAlert: l, showConfirm: s} = Be()
      , [w,S] = $("")
      , [I,M] = $(60)
      , [b,v] = $( () => localStorage.getItem("countdownName") || "")
      , [E,f] = $( () => localStorage.getItem("countdownDate") || "")
      , _ = !t || n
      , y = T(async k => {
        if (k === 2 && o && !await s("时钟模式是否支持局刷以实际效果为准，三色屏不建议长期开启时钟，长期局刷可能影响屏幕寿命或者烧屏，是否继续？", "提醒"))
            return;
        const D = new Date().getTime() / 1e3
          , U = new Uint8Array([D >> 24 & 255, D >> 16 & 255, D >> 8 & 255, D & 255, -(new Date().getTimezoneOffset() / 60), k]);
        await a(be.SET_TIME, U) && i("指令已发送！屏幕刷新完成前请不要操作。")
    }
    , [o, a, i])
      , F = T(async () => {
        await s("是否清除屏幕内容（刷为白色）?") && await a(be.CLEAR) && i("指令已发送！屏幕刷新完成前请不要操作。")
    }
    , [a, i])
      , W = T(async () => {
        if (w === "")
            return;
        const k = jn(w);
        if (k[0] == 152 && r < k.length)
            for (let D = 1; D < k.length; D += r - 2) {
                const U = k.slice(D, D + r - 2);
                await a(152, [D - 1, ...U])
            }
        else
            await a(k[0], k.length > 1 ? k.slice(1) : null)
    }
    , [w, a, r])
      , J = T(k => {
        h(D => D === k ? -1 : k)
    }
    , [h])
      , le = T(async () => {
        if (!b)
            return null;
        try {
            const k = await fetch("/render-text", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Machine-Id": m.current || ""
                },
                body: JSON.stringify({
                    text: b,
                    font: "Arial",
                    size: 12,
                    bold: !0
                })
            });
            if (!k.ok)
                return null;
            const D = await k.json()
              , U = atob(D.bitmap)
              , re = new Uint8Array(U.length);
            for (let P = 0; P < U.length; P++)
                re[P] = U.charCodeAt(P) & 255;
            return {
                width: D.width,
                height: D.height,
                bitmap: re
            }
        } catch {
            return i("渲染倒计时文本失败！", "⚠️"),
            null
        }
    }
    , [b, m])
      , pe = T(async () => {
        if (!b || !E) {
            l("请输入倒计时名称和日期！");
            return
        }
        const k = await le();
        if (!k)
            return;
        if (k.bitmap.length > 256) {
            l("文字过长，建议不超过 8 个中文字符。");
            return
        }
        const D = new Date(E);
        D.setHours(0, 0, 0, 0);
        const U = Math.floor(D.getTime() / 1e3) + -(new Date().getTimezoneOffset() / 60) * 3600;
        localStorage.setItem("countdownName", b),
        localStorage.setItem("countdownDate", E);
        const re = r - 2
          , P = [0, U >> 24 & 255, U >> 16 & 255, U >> 8 & 255, U & 255, k.width & 255, k.height & 255]
          , O = Math.min(k.bitmap.length, re - P.length)
          , _e = [...P, ...k.bitmap.slice(0, O)];
        await a(be.SET_COUNTDOWN, _e);
        let B = O;
        for (; B < k.bitmap.length; ) {
            const K = k.bitmap.length - B
              , V = Math.min(K, re - 1)
              , oe = [1, ...k.bitmap.slice(B, B + V)];
            await a(be.SET_COUNTDOWN, oe),
            B += V
        }
        l("倒计时已设置！稍后屏幕将自动刷新。")
    }
    , [b, E, r])
      , A = T(async () => {
        await s("是否清除倒计时？") && (await a(be.SET_COUNTDOWN, [255]),
        localStorage.removeItem("countdownName"),
        localStorage.removeItem("countdownDate"),
        v(""),
        f(""),
        l("倒计时已清除！稍后屏幕将自动刷新。"))
    }
    , [a, i, s])
      , N = p >= 0 && (x.usedMask & 1 << p) !== 0;
    return c("div", {
        className: "card",
        children: [c("div", {
            className: "card-header",
            children: [c(dr, {
                size: 15
            }), "设备控制"]
        }), c("div", {
            className: "card-body",
            children: [c("div", {
                className: "flex-container",
                children: c("div", {
                    className: "flex-group",
                    children: [c("button", {
                        type: "button",
                        className: "primary",
                        disabled: _,
                        onClick: () => y(1),
                        children: "日历模式"
                    }), c("button", {
                        type: "button",
                        className: "primary",
                        disabled: _,
                        onClick: () => y(2),
                        children: o ? "时钟模式" : "刷新模式"
                    }), c("button", {
                        type: "button",
                        disabled: _,
                        onClick: F,
                        children: "清除屏幕"
                    })]
                })
            }), e && c(Ne, {
                children: [c("hr", {
                    className: "divider"
                }), c("div", {
                    className: "flex-container",
                    children: [c("div", {
                        className: "flex-group",
                        children: [c("button", {
                            type: "button",
                            className: "primary",
                            disabled: _,
                            onClick: async () => {
                                await s("是否重启设备？", "提示") && await a(be.SYS_RESET)
                            }
                            ,
                            children: "重启设备"
                        }), c("button", {
                            type: "button",
                            className: "danger",
                            disabled: _,
                            onClick: async () => {
                                await s("此操作将会擦除所有用户设置，恢复到刚刷机后的状态，是否继续？", "警告") && await a(be.CFG_ERASE)
                            }
                            ,
                            children: "重置设备"
                        })]
                    }), c("div", {
                        className: "flex-group right",
                        children: [c("input", {
                            type: "text",
                            value: w,
                            onChange: k => S(k.target.value)
                        }), c("button", {
                            type: "button",
                            className: "primary",
                            disabled: _,
                            onClick: W,
                            children: "发送命令"
                        })]
                    })]
                })]
            }), c("hr", {
                className: "divider"
            }), c("div", {
                className: "flex-container",
                children: [c("div", {
                    className: "flex-group",
                    children: [c(Rr, {
                        size: 15
                    }), c("label", {
                        children: "倒计时:"
                    }), c("input", {
                        type: "text",
                        value: b,
                        placeholder: "事件名称",
                        style: {
                            maxWidth: "150px"
                        },
                        onChange: k => v(k.target.value)
                    })]
                }), c("div", {
                    className: "flex-group",
                    children: [c("label", {
                        children: "日期:"
                    }), c("input", {
                        type: "date",
                        value: E,
                        onChange: k => f(k.target.value)
                    }), c("button", {
                        type: "button",
                        className: "primary",
                        disabled: _ || !b || !E,
                        onClick: pe,
                        children: "设置"
                    }), c("button", {
                        type: "button",
                        disabled: _,
                        onClick: A,
                        children: "清除"
                    })]
                })]
            }), x.count > 0 && c(Ne, {
                children: [c("hr", {
                    className: "divider"
                }), c("div", {
                    className: "flex-container outline",
                    style: {
                        display: "block"
                    },
                    children: [c("div", {
                        className: "flex-container",
                        children: c("div", {
                            className: "flex-group",
                            children: [c("label", {
                                children: "选择图片槽位:"
                            }), N && c(Ne, {
                                children: [c("button", {
                                    type: "button",
                                    className: "primary small",
                                    disabled: _,
                                    onClick: async () => {
                                        await a(be.SET_SLOT, [1, p]),
                                        y(0)
                                    }
                                    ,
                                    children: "显示槽位"
                                }), c("button", {
                                    type: "button",
                                    className: "danger small",
                                    disabled: _,
                                    onClick: async () => {
                                        await s(`是否确认删除槽位 ${p} 的图片？此操作不可恢复！`, "警告") && await a(be.FREE_SLOT, [p])
                                    }
                                    ,
                                    children: "删除槽位"
                                })]
                            })]
                        })
                    }), c("div", {
                        className: "flex-container",
                        children: c("div", {
                            className: "flex-group",
                            children: Array.from({
                                length: x.count
                            }, (k, D) => {
                                const U = (x.usedMask & 1 << D) !== 0;
                                return c("button", {
                                    type: "button",
                                    className: D === p ? "primary" : "",
                                    onClick: () => J(D),
                                    children: [U ? c(lr, {
                                        size: "12"
                                    }) : c(Tr, {
                                        size: "12"
                                    }), " 槽位 ", D]
                                }, D)
                            }
                            )
                        })
                    }), c("hr", {
                        className: "divider"
                    }), c("div", {
                        className: "flex-container",
                        children: c("div", {
                            className: "flex-group",
                            children: [c("label", {
                                children: "间隔:"
                            }), c("input", {
                                type: "number",
                                value: I,
                                min: "1",
                                style: {
                                    maxWidth: "80px"
                                },
                                onChange: k => M(parseInt(k.target.value))
                            }), " 分钟", c("button", {
                                type: "button",
                                className: "primary",
                                disabled: _,
                                onClick: async () => {
                                    await s(`即将开启图片轮播模式，间隔：${I} 分钟，是否继续？点击设备控制下的其它模式按钮可退出轮播模式。`, "提示") && await a(be.SET_SLIDE, [I >> 8 & 255, I & 255])
                                }
                                ,
                                children: "启动轮播"
                            })]
                        })
                    })]
                })]
            })]
        })]
    })
}
const yt = [{
    name: "黑色",
    r: 0,
    g: 0,
    b: 0,
    value: 0
}, {
    name: "白色",
    r: 255,
    g: 255,
    b: 255,
    value: 1
}, {
    name: "黄色",
    r: 255,
    g: 255,
    b: 0,
    value: 2
}, {
    name: "红色",
    r: 255,
    g: 0,
    b: 0,
    value: 3
}, {
    name: "蓝色",
    r: 0,
    g: 0,
    b: 255,
    value: 5
}, {
    name: "绿色",
    r: 41,
    g: 204,
    b: 20,
    value: 6
}]
  , Yr = [{
    name: "黑色",
    r: 0,
    g: 0,
    b: 0,
    value: 0
}, {
    name: "白色",
    r: 255,
    g: 255,
    b: 255,
    value: 1
}, {
    name: "红色",
    r: 255,
    g: 0,
    b: 0,
    value: 3
}, {
    name: "黄色",
    r: 255,
    g: 255,
    b: 0,
    value: 2
}]
  , dt = [{
    name: "黑色",
    r: 0,
    g: 0,
    b: 0,
    value: 0
}, {
    name: "白色",
    r: 255,
    g: 255,
    b: 255,
    value: 1
}, {
    name: "红色",
    r: 255,
    g: 0,
    b: 0,
    value: 2
}]
  , It = [{
    name: "黑色",
    r: 0,
    g: 0,
    b: 0,
    value: 0
}, {
    name: "白色",
    r: 255,
    g: 255,
    b: 255,
    value: 1
}]
  , Jr = [{
    name: "黑色",
    r: 0,
    g: 0,
    b: 0,
    value: 0
}, {
    name: "深灰",
    r: 85,
    g: 85,
    b: 85,
    value: 1
}, {
    name: "浅灰",
    r: 170,
    g: 170,
    b: 170,
    value: 2
}, {
    name: "白色",
    r: 255,
    g: 255,
    b: 255,
    value: 3
}]
  , qr = Array.from({
    length: 16
}, (e, t) => ({
    name: `灰${t}`,
    r: t * 17,
    g: t * 17,
    b: t * 17,
    value: t
}));
function Gr(e, t) {
    const n = e.data
      , a = (t - 1) * 128;
    for (let i = 0; i < n.length; i += 4)
        n[i] = Math.min(255, Math.max(0, n[i] + a)),
        n[i + 1] = Math.min(255, Math.max(0, n[i + 1] + a)),
        n[i + 2] = Math.min(255, Math.max(0, n[i + 2] + a));
    return e
}
function Kr(e, t) {
    const n = e.data;
    for (let a = 0; a < n.length; a += 4)
        n[a] = Math.min(255, Math.max(0, (n[a] - 128) * t + 128)),
        n[a + 1] = Math.min(255, Math.max(0, (n[a + 1] - 128) * t + 128)),
        n[a + 2] = Math.min(255, Math.max(0, (n[a + 2] - 128) * t + 128));
    return e
}
function mn(e, t, n) {
    e = e / 255,
    t = t / 255,
    n = n / 255,
    e = e > .04045 ? Math.pow((e + .055) / 1.055, 2.4) : e / 12.92,
    t = t > .04045 ? Math.pow((t + .055) / 1.055, 2.4) : t / 12.92,
    n = n > .04045 ? Math.pow((n + .055) / 1.055, 2.4) : n / 12.92,
    e *= 100,
    t *= 100,
    n *= 100;
    let a = e * .4124 + t * .3576 + n * .1805
      , i = e * .2126 + t * .7152 + n * .0722
      , r = e * .0193 + t * .1192 + n * .9505;
    a /= 95.047,
    i /= 100,
    r /= 108.883,
    a = a > .008856 ? Math.pow(a, 1 / 3) : 7.787 * a + 16 / 116,
    i = i > .008856 ? Math.pow(i, 1 / 3) : 7.787 * i + 16 / 116,
    r = r > .008856 ? Math.pow(r, 1 / 3) : 7.787 * r + 16 / 116;
    const o = 116 * i - 16
      , x = 500 * (a - i)
      , p = 200 * (i - r);
    return {
        l: o,
        a: x,
        b: p
    }
}
function Zr(e, t) {
    const n = e.l - t.l
      , a = e.a - t.a
      , i = e.b - t.b;
    return Math.sqrt(.2 * n * n + 3 * a * a + 3 * i * i)
}
function at(e, t, n, a) {
    let i;
    if (a === "fourColor" ? i = Yr : a === "threeColor" ? i = dt : a === "blackWhiteColor" ? i = It : a === "fourGray" ? i = Jr : a === "sixteenGray" ? i = qr : i = yt,
    a === "blackWhiteColor")
        return .299 * e + .587 * t + .114 * n < 128 ? It[0] : It[1];
    if (a === "fourGray" || a === "sixteenGray") {
        const p = .299 * e + .587 * t + .114 * n;
        return i.reduce( (h, m) => Math.abs(h.r - p) <= Math.abs(m.r - p) ? h : m)
    }
    if (a !== "fourColor" && a !== "threeColor" && e < 50 && t < 150 && n > 100)
        return yt[4];
    if (a === "threeColor")
        return e > 120 && e > t * 1.5 && e > n * 1.5 ? dt[2] : .299 * e + .587 * t + .114 * n < 128 ? dt[0] : dt[1];
    const r = mn(e, t, n);
    let o = 1 / 0
      , x = i[0];
    for (const p of i) {
        const h = mn(p.r, p.g, p.b)
          , m = Zr(r, h);
        m < o && (o = m,
        x = p)
    }
    return x
}
function Qr(e, t, n, a, i, r) {
    e[t] = Math.min(255, Math.max(0, e[t] + n * r)),
    e[t + 1] = Math.min(255, Math.max(0, e[t + 1] + a * r)),
    e[t + 2] = Math.min(255, Math.max(0, e[t + 2] + i * r))
}
function qe(e, t, n, a, i=!1) {
    const r = e.width
      , o = e.height
      , x = e.data
      , p = new Uint8ClampedArray(x);
    for (let h = 0; h < o; h++)
        for (let m = 0; m < r; m++) {
            const l = (h * r + m) * 4
              , s = p[l]
              , w = p[l + 1]
              , S = p[l + 2]
              , I = at(s, w, S, n);
            i && (x[l] = I.r,
            x[l + 1] = I.g,
            x[l + 2] = I.b);
            const M = (s - I.r) * t
              , b = (w - I.g) * t
              , v = (S - I.b) * t;
            for (const [E,f,_] of a) {
                const y = m + E
                  , F = h + f;
                if (y >= 0 && y < r && F >= 0 && F < o) {
                    const W = (F * r + y) * 4;
                    Qr(p, W, M, b, v, _)
                }
            }
        }
    if (!i)
        for (let h = 0; h < o; h++)
            for (let m = 0; m < r; m++) {
                const l = (h * r + m) * 4
                  , s = at(p[l], p[l + 1], p[l + 2], n);
                x[l] = s.r,
                x[l + 1] = s.g,
                x[l + 2] = s.b
            }
    return e
}
function eo(e, t, n) {
    return qe(e, t, n, [[1, 0, .4375], [-1, 1, .1875], [0, 1, .3125], [1, 1, .0625]], !1)
}
function to(e, t, n) {
    return qe(e, t, n, [[1, 0, .125], [2, 0, .125], [-1, 1, .125], [0, 1, .125], [1, 1, .125], [0, 2, .125]], !0)
}
function no(e, t, n) {
    return qe(e, t, n, [[1, 0, .19047619047619047], [2, 0, .09523809523809523], [-2, 1, .047619047619047616], [-1, 1, .09523809523809523], [0, 1, .19047619047619047], [1, 1, .09523809523809523], [2, 1, .047619047619047616], [-2, 2, .023809523809523808], [-1, 2, .047619047619047616], [0, 2, .09523809523809523], [1, 2, .047619047619047616], [2, 2, .023809523809523808]], !1)
}
function ao(e, t, n) {
    return qe(e, t, n, [[1, 0, .14583333333333334], [2, 0, .10416666666666667], [-2, 1, .0625], [-1, 1, .10416666666666667], [0, 1, .14583333333333334], [1, 1, .10416666666666667], [2, 1, .0625], [-2, 2, .020833333333333332], [-1, 2, .0625], [0, 2, .10416666666666667], [1, 2, .0625], [2, 2, .020833333333333332]], !0)
}
function ro(e, t, n) {
    return qe(e, t, n, [[1, 0, .25], [2, 0, .125], [-2, 1, .0625], [-1, 1, .125], [0, 1, .25], [1, 1, .125], [2, 1, .0625]], !1)
}
function oo(e, t, n) {
    return qe(e, t, n, [[1, 0, .15625], [2, 0, .09375], [-2, 1, .0625], [-1, 1, .125], [0, 1, .15625], [1, 1, .125], [2, 1, .0625], [-1, 2, .0625], [0, 2, .09375], [1, 2, .0625]], !1)
}
function co(e, t, n) {
    const a = e.width
      , i = e.height
      , r = e.data
      , o = [[0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26], [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22], [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25], [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]]
      , x = 8
      , p = 64;
    for (let h = 0; h < i; h++)
        for (let m = 0; m < a; m++) {
            const l = (h * a + m) * 4
              , s = r[l]
              , w = r[l + 1]
              , S = r[l + 2]
              , I = m % x
              , M = h % x
              , b = o[M][I] / p * 255
              , v = s + (b - 127.5) * t
              , E = w + (b - 127.5) * t
              , f = S + (b - 127.5) * t
              , _ = Math.min(255, Math.max(0, v))
              , y = Math.min(255, Math.max(0, E))
              , F = Math.min(255, Math.max(0, f))
              , W = at(_, y, F, n);
            r[l] = W.r,
            r[l + 1] = W.g,
            r[l + 2] = W.b
        }
    return e
}
function Yn(e, t, n, a) {
    switch (t) {
    case "floydSteinberg":
        return eo(e, n, a);
    case "atkinson":
        return to(e, n, a);
    case "stucki":
        return no(e, n, a);
    case "jarvis":
        return ao(e, n, a);
    case "burkes":
        return ro(e, n, a);
    case "sierra":
        return oo(e, n, a);
    case "bayer":
        return co(e, n, a);
    case "none":
    default:
        return e
    }
}
function Jn(e, t, n, a) {
    const i = new ImageData(t,n)
      , r = i.data;
    if (a === "sixColor")
        for (let o = 0; o < n; o++)
            for (let x = 0; x < t; x++) {
                const p = o * t + x >> 1
                  , h = x % 2 === 0 ? e[p] >> 4 & 15 : e[p] & 15
                  , m = yt.find(s => s.value === h) || yt[1]
                  , l = (o * t + x) * 4;
                r[l] = m.r,
                r[l + 1] = m.g,
                r[l + 2] = m.b,
                r[l + 3] = 255
            }
    else if (a === "fourColor") {
        const o = [{
            value: 0,
            r: 0,
            g: 0,
            b: 0
        }, {
            value: 1,
            r: 255,
            g: 255,
            b: 255
        }, {
            value: 3,
            r: 255,
            g: 0,
            b: 0
        }, {
            value: 2,
            r: 255,
            g: 255,
            b: 0
        }];
        for (let x = 0; x < n; x++)
            for (let p = 0; p < t; p++) {
                const h = (x * t + p) / 4 | 0
                  , m = 6 - p % 4 * 2
                  , l = e[h] >> m & 3
                  , s = o.find(S => S.value === l) || o[1]
                  , w = (x * t + p) * 4;
                r[w] = s.r,
                r[w + 1] = s.g,
                r[w + 2] = s.b,
                r[w + 3] = 255
            }
    } else if (a === "blackWhiteColor") {
        const o = Math.ceil(t / 8);
        for (let x = 0; x < n; x++)
            for (let p = 0; p < t; p++) {
                const h = x * o + Math.floor(p / 8)
                  , m = 7 - p % 8
                  , l = e[h] >> m & 1
                  , s = (x * t + p) * 4;
                r[s] = l ? 255 : 0,
                r[s + 1] = l ? 255 : 0,
                r[s + 2] = l ? 255 : 0,
                r[s + 3] = 255
            }
    } else if (a === "fourGray")
        for (let o = 0; o < n; o++)
            for (let x = 0; x < t; x++) {
                const p = o * t + x >> 2
                  , h = 6 - x % 4 * 2
                  , l = (e[p] >> h & 3) * 85
                  , s = (o * t + x) * 4;
                r[s] = l,
                r[s + 1] = l,
                r[s + 2] = l,
                r[s + 3] = 255
            }
    else if (a === "sixteenGray")
        for (let o = 0; o < n; o++)
            for (let x = 0; x < t; x++) {
                const p = o * t + x >> 1
                  , m = (x % 2 === 0 ? e[p] >> 4 & 15 : e[p] & 15) * 17
                  , l = (o * t + x) * 4;
                r[l] = m,
                r[l + 1] = m,
                r[l + 2] = m,
                r[l + 3] = 255
            }
    else if (a === "threeColor") {
        const o = Math.ceil(t / 8)
          , x = e.slice(0, o * n)
          , p = e.slice(o * n);
        for (let h = 0; h < n; h++)
            for (let m = 0; m < t; m++) {
                const l = h * o + Math.floor(m / 8)
                  , s = 7 - m % 8
                  , w = x[l] >> s & 1
                  , S = p[l] >> s & 1
                  , I = (h * t + m) * 4;
                S ? (r[I] = w ? 255 : 0,
                r[I + 1] = w ? 255 : 0,
                r[I + 2] = w ? 255 : 0) : (r[I] = 255,
                r[I + 1] = 0,
                r[I + 2] = 0),
                r[I + 3] = 255
            }
    }
    return i
}
function _t(e, t) {
    const n = e.width
      , a = e.height
      , i = e.data;
    let r;
    if (t === "sixColor") {
        r = new Uint8Array(Math.ceil(n * a / 2));
        for (let o = 0; o < a; o++)
            for (let x = 0; x < n; x++) {
                const p = (o * n + x) * 4
                  , h = i[p]
                  , m = i[p + 1]
                  , l = i[p + 2]
                  , w = at(h, m, l, t).value
                  , S = o * n + x >> 1;
                x % 2 === 0 ? r[S] |= w << 4 : r[S] |= w
            }
    } else if (t === "fourColor") {
        r = new Uint8Array(Math.ceil(n * a / 4));
        for (let o = 0; o < a; o++)
            for (let x = 0; x < n; x++) {
                const p = (o * n + x) * 4
                  , h = i[p]
                  , m = i[p + 1]
                  , l = i[p + 2]
                  , w = at(h, m, l, t).value
                  , S = (o * n + x) / 4 | 0
                  , I = 6 - x % 4 * 2;
                r[S] |= w << I
            }
    } else if (t === "blackWhiteColor") {
        const o = Math.ceil(n / 8);
        r = new Uint8Array(o * a);
        const x = 140;
        for (let p = 0; p < a; p++)
            for (let h = 0; h < n; h++) {
                const m = (p * n + h) * 4
                  , l = i[m]
                  , s = i[m + 1]
                  , w = i[m + 2]
                  , I = Math.round(.299 * l + .587 * s + .114 * w) >= x ? 1 : 0
                  , M = p * o + Math.floor(h / 8)
                  , b = 7 - h % 8;
                r[M] |= I << b
            }
    } else if (t === "fourGray") {
        r = new Uint8Array(Math.ceil(n * a / 4));
        for (let o = 0; o < a; o++)
            for (let x = 0; x < n; x++) {
                const p = (o * n + x) * 4
                  , h = Math.round(.299 * i[p] + .587 * i[p + 1] + .114 * i[p + 2])
                  , m = Math.min(3, Math.round(h / 85))
                  , l = o * n + x >> 2
                  , s = 6 - x % 4 * 2;
                r[l] |= m << s
            }
    } else if (t === "sixteenGray") {
        r = new Uint8Array(Math.ceil(n * a / 2));
        for (let o = 0; o < a; o++)
            for (let x = 0; x < n; x++) {
                const p = (o * n + x) * 4
                  , h = Math.round(.299 * i[p] + .587 * i[p + 1] + .114 * i[p + 2])
                  , m = Math.min(15, Math.round(h / 17))
                  , l = o * n + x >> 1;
                x % 2 === 0 ? r[l] |= m << 4 : r[l] |= m
            }
    } else if (t === "threeColor") {
        const o = Math.ceil(n / 8)
          , x = 140
          , p = 160
          , h = new Uint8Array(a * o)
          , m = new Uint8Array(a * o);
        for (let l = 0; l < a; l++)
            for (let s = 0; s < n; s++) {
                const w = (l * n + s) * 4
                  , S = i[w]
                  , I = i[w + 1]
                  , M = i[w + 2]
                  , v = Math.round(.299 * S + .587 * I + .114 * M) >= x ? 1 : 0
                  , E = l * o + Math.floor(s / 8)
                  , f = 7 - s % 8;
                v ? h[E] |= 1 << f : h[E] &= ~(1 << f);
                const _ = S > p && S > I && S > M ? 0 : 1
                  , y = l * o + Math.floor(s / 8)
                  , F = 7 - s % 8;
                _ ? m[y] |= 1 << F : m[y] &= ~(1 << F)
            }
        r = new Uint8Array(h.length + m.length),
        r.set(h, 0),
        r.set(m, h.length)
    }
    return r
}
class io {
    constructor(t, n, a) {
        this.ctx = t,
        this.width = n,
        this.height = a
    }
    async renderElement(t) {
        if (!t.type) {
            console.warn("Element missing type:", t);
            return
        }
        switch (t.type.toLowerCase()) {
        case "text":
            this.renderText(t);
            break;
        case "line":
            this.renderLine(t);
            break;
        case "rect":
        case "rectangle":
            this.renderRectangle(t);
            break;
        case "circle":
            this.renderCircle(t);
            break;
        case "ellipse":
            this.renderEllipse(t);
            break;
        case "image":
            await this.renderImage(t);
            break;
        case "polygon":
            this.renderPolygon(t);
            break;
        case "path":
            this.renderPath(t);
            break;
        default:
            console.warn("Unknown element type:", t.type)
        }
    }
    renderText(t) {
        const {x: n=0, y: a=0, text: i="", font: r="16px Arial", color: o="#000000", align: x="left", baseline: p="alphabetic", bold: h=!1, italic: m=!1, maxWidth: l} = t;
        this.ctx.save();
        let s = "";
        m && (s += "italic "),
        h && (s += "bold "),
        this.ctx.font = s + r,
        this.ctx.fillStyle = o,
        this.ctx.textAlign = x,
        this.ctx.textBaseline = p,
        l !== void 0 ? this.ctx.fillText(i, n, a, l) : this.ctx.fillText(i, n, a),
        this.ctx.restore()
    }
    renderLine(t) {
        const {x1: n=0, y1: a=0, x2: i=0, y2: r=0, color: o="#000000", width: x=1, dash: p=null, lineCap: h="round", lineJoin: m="round"} = t;
        this.ctx.save(),
        this.ctx.strokeStyle = o,
        this.ctx.lineWidth = x,
        this.ctx.lineCap = h,
        this.ctx.lineJoin = m,
        p && Array.isArray(p) && this.ctx.setLineDash(p),
        this.ctx.beginPath(),
        this.ctx.moveTo(n, a),
        this.ctx.lineTo(i, r),
        this.ctx.stroke(),
        this.ctx.restore()
    }
    renderRectangle(t) {
        const {x: n=0, y: a=0, width: i=0, height: r=0, color: o="#000000", fill: x=!1, strokeWidth: p=1, radius: h=0} = t;
        this.ctx.save(),
        h > 0 ? (this.ctx.beginPath(),
        this.ctx.moveTo(n + h, a),
        this.ctx.lineTo(n + i - h, a),
        this.ctx.arcTo(n + i, a, n + i, a + h, h),
        this.ctx.lineTo(n + i, a + r - h),
        this.ctx.arcTo(n + i, a + r, n + i - h, a + r, h),
        this.ctx.lineTo(n + h, a + r),
        this.ctx.arcTo(n, a + r, n, a + r - h, h),
        this.ctx.lineTo(n, a + h),
        this.ctx.arcTo(n, a, n + h, a, h),
        this.ctx.closePath(),
        x ? (this.ctx.fillStyle = o,
        this.ctx.fill()) : (this.ctx.strokeStyle = o,
        this.ctx.lineWidth = p,
        this.ctx.stroke())) : x ? (this.ctx.fillStyle = o,
        this.ctx.fillRect(n, a, i, r)) : (this.ctx.strokeStyle = o,
        this.ctx.lineWidth = p,
        this.ctx.strokeRect(n, a, i, r)),
        this.ctx.restore()
    }
    renderCircle(t) {
        const {x: n=0, y: a=0, radius: i=0, color: r="#000000", fill: o=!1, strokeWidth: x=1} = t;
        this.ctx.save(),
        this.ctx.beginPath(),
        this.ctx.arc(n, a, i, 0, 2 * Math.PI),
        o ? (this.ctx.fillStyle = r,
        this.ctx.fill()) : (this.ctx.strokeStyle = r,
        this.ctx.lineWidth = x,
        this.ctx.stroke()),
        this.ctx.restore()
    }
    renderEllipse(t) {
        const {x: n=0, y: a=0, radiusX: i=0, radiusY: r=0, rotation: o=0, color: x="#000000", fill: p=!1, strokeWidth: h=1} = t;
        this.ctx.save(),
        this.ctx.beginPath(),
        this.ctx.ellipse(n, a, i, r, o * Math.PI / 180, 0, 2 * Math.PI),
        p ? (this.ctx.fillStyle = x,
        this.ctx.fill()) : (this.ctx.strokeStyle = x,
        this.ctx.lineWidth = h,
        this.ctx.stroke()),
        this.ctx.restore()
    }
    async renderImage(t) {
        const {x: n=0, y: a=0, width: i, height: r, src: o, dither: x} = t;
        if (!o) {
            console.warn("Image element missing src");
            return
        }
        return new Promise( (p, h) => {
            const m = new Image;
            m.crossOrigin = "anonymous",
            m.onload = () => {
                const l = i !== void 0 ? i : m.width
                  , s = r !== void 0 ? r : m.height;
                if (x) {
                    const w = document.createElement("canvas");
                    w.width = l,
                    w.height = s;
                    const S = w.getContext("2d");
                    S.drawImage(m, 0, 0, l, s);
                    const I = S.getImageData(0, 0, l, s)
                      , M = x.algorithm || "floydSteinberg"
                      , b = x.strength !== void 0 ? x.strength : 1
                      , v = x.mode || "blackWhiteColor"
                      , E = Yn(I, M, b, v)
                      , f = _t(E, v)
                      , _ = Jn(f, l, s, v);
                    S.putImageData(_, 0, 0),
                    this.ctx.drawImage(w, n, a, l, s)
                } else
                    this.ctx.drawImage(m, n, a, l, s);
                p()
            }
            ,
            m.onerror = () => {
                console.warn("Failed to load image:", o),
                p()
            }
            ,
            m.src = o
        }
        )
    }
    renderPolygon(t) {
        const {points: n=[], color: a="#000000", fill: i=!1, strokeWidth: r=1} = t;
        if (!Array.isArray(n) || n.length < 2) {
            console.warn("Polygon needs at least 2 points");
            return
        }
        this.ctx.save(),
        this.ctx.beginPath(),
        this.ctx.moveTo(n[0].x, n[0].y);
        for (let o = 1; o < n.length; o++)
            this.ctx.lineTo(n[o].x, n[o].y);
        this.ctx.closePath(),
        i ? (this.ctx.fillStyle = a,
        this.ctx.fill()) : (this.ctx.strokeStyle = a,
        this.ctx.lineWidth = r,
        this.ctx.stroke()),
        this.ctx.restore()
    }
    renderPath(t) {
        const {d: n="", color: a="#000000", fill: i=!1, strokeWidth: r=1} = t;
        if (!n) {
            console.warn("Path element missing data");
            return
        }
        this.ctx.save();
        const o = new Path2D(n);
        i ? (this.ctx.fillStyle = a,
        this.ctx.fill(o)) : (this.ctx.strokeStyle = a,
        this.ctx.lineWidth = r,
        this.ctx.stroke(o)),
        this.ctx.restore()
    }
}
const qn = Oe;
(function(e, t) {
    const n = Oe
      , a = e();
    for (; ; )
        try {
            if (-parseInt(n(480)) / 1 * (parseInt(n(439)) / 2) + -parseInt(n(436)) / 3 * (-parseInt(n(426)) / 4) + -parseInt(n(470)) / 5 * (-parseInt(n(447)) / 6) + parseInt(n(490)) / 7 + parseInt(n(414)) / 8 + parseInt(n(506)) / 9 * (parseInt(n(476)) / 10) + -parseInt(n(539)) / 11 * (parseInt(n(495)) / 12) === t)
                break;
            a.push(a.shift())
        } catch {
            a.push(a.shift())
        }
}
)(wt, 919229);
const lo = (function() {
    let e = !0;
    return function(t, n) {
        const a = e ? function() {
            const i = Oe;
            if (n) {
                const r = n[i(497)](t, arguments);
                return n = null,
                r
            }
        }
        : function() {}
        ;
        return e = !1,
        a
    }
}
)()
  , so = lo(void 0, function() {
    const e = Oe
      , t = function() {
        const b = Oe;
        let v;
        try {
            v = Function(b(428) + b(531) + ");")()
        } catch {
            v = window
        }
        return v
    }
      , n = t()
      , a = new RegExp("[qCRVVXMUkOUkTwxjERUCMJTWFCEubRZLLgbFZCFxr]","g")
      , i = e(502)[e(496)](a, "")[e(434)](";");
    let r, o, x, p;
    const h = function(b, v, E) {
        const f = e;
        if (b[f(499)] != v)
            return !1;
        for (let _ = 0; _ < v; _++)
            for (let y = 0; y < E[f(499)]; y += 2)
                if (_ == E[y] && b.charCodeAt(_) != E[y + 1])
                    return !1;
        return !0
    }
      , m = function(b, v, E) {
        return h(v, E, b)
    }
      , l = function(b, v, E) {
        return m(v, b, E)
    }
      , s = function(b, v, E) {
        return l(v, E, b)
    };
    for (let b in n)
        if (h(b, 8, [7, 116, 5, 101, 3, 117, 0, 100])) {
            r = b;
            break
        }
    for (let b in n[r])
        if (s(6, b, [5, 110, 0, 100])) {
            o = b;
            break
        }
    for (let b in n[r])
        if (l(b, [7, 110, 0, 108], 8)) {
            x = b;
            break
        }
    if (!("~" > o)) {
        for (let b in n[r][x])
            if (m([7, 101, 0, 104], b, 8)) {
                p = b;
                break
            }
    }
    if (!r || !n[r])
        return;
    const w = n[r][o]
      , S = !!n[r][x] && n[r][x][p]
      , I = w || S;
    if (!I)
        return;
    let M = !1;
    for (let b = 0; b < i[e(499)]; b++) {
        const v = i[b]
          , E = v[0] === String[e(550)](46) ? v[e(429)](1) : v
          , f = I[e(499)] - E.length
          , _ = I[e(438)](E, f);
        _ !== -1 && _ === f && (I[e(499)] == v[e(499)] || v[e(438)](".") === 0) && (M = !0)
    }
    if (!M) {
        const b = new RegExp(e(453),"g")
          , v = e(433)[e(496)](b, "");
        n[r][x] = v
    }
});
so();
function wt() {
    const e = ["getImageData", "createElement", "89331RYFwQQ", "preventDefault", "cursor", "top", "remove", "textBold", "updateCursor", "removeChild", "dragOffsetX", "type", "painting", "fromCharCode", "key", "current", "appendChild", "templateVars", "text-placement-mode", "elements", "拖动新添加文字可调整位置", "brushCursor", "shiftKey", "Error deleting template variables:", "bold", "50%", "2533824aLHZiA", "textItalic", "line", "bold ", "border", "keyboard", "default", "boxShadow", "none", "putImageData", "willChange", "italic ", "4GSXloy", "height", "return (function() ", "slice", "rgba(255, 255, 255, 0.2)", "dispatchEvent", "brushSize", "IhWttpAsR:w//fEepdWixJyP.LAcNnobvglTGwTDvPCIvJbluqgXoQ", "split", "eraser", "2762157DWQSwE", "removeEventListener", "indexOf", "44134SqRvdP", "translate(", "touchMove", "translate(-50%, -50%)", "parse", "mouseleave", "push", "left", "518712OCAdCj", "px) translate(-50%, -50%)", "circle", "bottom", "backgroundColor", "imageData", "[IWARwfEWxJPLANobvglTGwTDvPCIvJbluqgXoQ]", "10000", "text", "isTextPlacementMode", "Error saving template variables:", "data-tool", "touchmove", "width", "touchEnd", "pointerEvents", "shift", "mouseenter", "mousemove", "getItem", "touchStart", "clientX", "min", "5wuIGHk", "brush", "setAttribute", "mousedown", "getAttribute", "font", "136490eEgftk", "historyStack", "transform", "touches", "14boaBPF", "brush-cursor", "getBoundingClientRect", "mouseup", "click", "startPaint", "right", "italic", "1px solid white", "template", "9378824iXacQz", "Arial", "position", "historyStep", "canvasClick", "2928oZVoKE", "replace", "apply", "relative", "length", "isDraggingText", "keydown", "qCeRpdViyV.XcnM;UlokOUkTcwxjalhERostUCMJTWFCEubRZLLgbFZCFxr", "classList", "transparent", "paint", "360XfpnkA", "metaKey", "zIndex", "display", "lastY", "div", "px, ", "parentNode", "draggingCanvasContext", "touchstart", "ctrlKey", "style", "match", "lastX", "currentTool", "dragOffsetY", "setItem", "brushColor", "stringify", "selectedTextElement", "px ", "点击画布放置文字", "renderElement", "pendingText", "error", '{}.constructor("return this")( )', "block", "clientY", "endPaint", "2px solid rgba(255, 0, 0, 0.7)", "addEventListener"];
    return wt = function() {
        return e
    }
    ,
    wt()
}
const xo = 100
  , Ze = qn(405);
function Oe(e, t) {
    const n = wt();
    return Oe = function(a, i) {
        return a = a - 404,
        n[a]
    }
    ,
    Oe(e, t)
}
function uo(e, t) {
    const n = qn
      , {showAlert: a} = Be()
      , [i,r] = $("")
      , [o,x] = $(null)
      , [p,h] = $(!0)
      , [m,l] = $(!0)
      , s = te({
        elements: [],
        template: null,
        historyStack: [],
        historyStep: -1,
        painting: !1,
        lastX: 0,
        lastY: 0,
        brushColor: "#000000",
        brushSize: 2,
        currentTool: null,
        isTextPlacementMode: !1,
        textBold: !1,
        textItalic: !1,
        selectedTextElement: null,
        isDraggingText: !1,
        dragOffsetX: 0,
        dragOffsetY: 0,
        draggingCanvasContext: null,
        brushCursor: null,
        pendingText: null
    })[n(552)]
      , w = te(null)
      , S = te({})
      , I = te(null);
    !I.current && (I.current = {
        startPaint: d => S.current[n(485)](d),
        paint: d => S[n(552)][n(505)](d),
        endPaint: () => S[n(552)][n(534)](),
        canvasClick: d => S[n(552)][n(494)](d),
        keyboard: d => S.current[n(419)](d),
        updateCursor: d => S[n(552)][n(545)](d),
        touchStart: d => S[n(552)][n(467)](d),
        touchMove: d => S[n(552)][n(441)](d),
        touchEnd: d => S.current[n(461)](d)
    });
    const M = T( () => {
        const d = n;
        h(s[d(493)] <= 0),
        l(s[d(493)] >= s[d(477)].length - 1)
    }
    , [s])
      , b = T( (d=!1) => {
        const u = n
          , C = t[u(552)]
          , z = e[u(552)];
        !C || !z || (s.historyStack = s[u(477)][u(429)](0, s[u(493)] + 1),
        s[u(477)][u(445)]({
            imageData: C.getImageData(0, 0, z[u(460)], z.height),
            elements: JSON[u(443)](JSON[u(524)](s.elements)),
            dithered: d
        }),
        s[u(493)]++,
        s[u(477)][u(499)] > xo && (s[u(477)][u(463)](),
        s.historyStep--),
        M())
    }
    , [s, e, t, M])
      , v = T( () => {
        const d = n
          , u = s[d(493)]
          , C = s.historyStack;
        u >= 0 && u < C[d(499)] && (t[d(552)][d(423)](C[u][d(452)], 0, 0),
        s[d(407)] = JSON[d(443)](JSON[d(524)](C[u][d(407)])),
        M())
    }
    , [s, t, M])
      , E = T( () => {
        const d = n;
        s[d(477)] = [],
        s[d(493)] = -1,
        M()
    }
    , [s, M])
      , f = T( () => {
        const d = n;
        s[d(493)] > 0 && (s[d(493)]--,
        v())
    }
    , [s, v])
      , _ = T( () => {
        const d = n;
        s[d(493)] < s.historyStack.length - 1 && (s[d(493)]++,
        v())
    }
    , [s, v])
      , y = T( () => {
        const d = n;
        for (let u = s[d(477)][d(499)] - 1; u >= 0; u--)
            if (!s[d(477)][u].dithered)
                return s.historyStack[u][d(452)];
        return null
    }
    , [s])
      , F = T( () => {
        const d = n;
        s.isTextPlacementMode = !1,
        e[d(552)]?.[d(503)].remove(d(406)),
        s[d(500)] = !1,
        s[d(547)] = 0,
        s[d(521)] = 0,
        s[d(525)] = null,
        s.draggingCanvasContext = null
    }
    , [s, e])
      , W = T( (d, u) => {
        const C = n;
        s[C(520)] = d,
        x(d),
        r(u || ""),
        F()
    }
    , [s, F])
      , J = T( () => {
        const d = n
          , u = s[d(409)]
          , C = e[d(552)];
        if (!u || !C)
            return;
        const z = C[d(482)]()
          , j = Math[d(469)](z[d(460)] / C[d(460)], z[d(427)] / C.height)
          , ae = s[d(432)] * j;
        u.style[d(460)] = ae + "px",
        u[d(517)][d(427)] = ae + "px"
    }
    , [s, e])
      , le = T(d => {
        const u = n;
        s[u(523)] = d
    }
    , [s])
      , pe = T(d => {
        const u = n;
        s[u(432)] = d,
        J()
    }
    , [s, J])
      , A = T(d => {
        const u = n;
        s[u(544)] = d
    }
    , [s])
      , N = T(d => {
        s.textItalic = d
    }
    , [s])
      , k = T(async (d, u, C) => {
        const z = n;
        if (!(d || "").trim()) {
            await a("请输入文字内容");
            return
        }
        s[z(529)] = {
            text: d,
            fontFamily: u || z(491),
            fontSize: C || 16
        },
        s[z(456)] = !0,
        r(z(527)),
        e[z(552)]?.[z(503)].add(z(406))
    }
    , [s, e, a])
      , D = T(async () => {
        const d = n;
        if (s[d(489)])
            for (const u of s.elements)
                await s[d(489)].renderElement(u)
    }
    , [s])
      , U = T( () => {
        s.elements = []
    }
    , [s])
      , re = T( (d, u) => {
        const C = n;
        s[C(489)] && (s[C(489)][C(460)] = d,
        s[C(489)][C(427)] = u)
    }
    , [s])
      , P = T( (d, u) => {
        const C = n;
        try {
            const z = JSON.parse(localStorage[C(466)](Ze) || "{}");
            z[d] = u,
            localStorage[C(522)](Ze, JSON[C(524)](z))
        } catch (z) {
            console[C(530)](C(457), z)
        }
    }
    , [])
      , O = T(d => {
        const u = n;
        try {
            const C = JSON[u(443)](localStorage[u(466)](Ze) || "{}");
            C[d] && (delete C[d],
            localStorage[u(522)](Ze, JSON.stringify(C)))
        } catch (C) {
            console[u(530)](u(411), C)
        }
    }
    , [])
      , _e = T(d => {
        const u = n;
        try {
            return JSON[u(443)](localStorage[u(466)](Ze) || "{}")[d] || null
        } catch (C) {
            return console[u(530)]("Error loading template variables:", C),
            null
        }
    }
    , []);
    S[n(552)].startPaint = d => {
        const u = n;
        if (s[u(520)])
            if (s[u(520)] === "text") {
                const C = K(d);
                if (C && C === s[u(525)]) {
                    s[u(500)] = !0;
                    const {x: z, y: j} = B(d);
                    s[u(547)] = C.x - z,
                    s[u(521)] = C.y - j;
                    return
                }
            } else
                (s[u(520)] === u(471) || s[u(520)] === u(435)) && (s[u(549)] = !0,
                V(d))
    }
    ,
    S[n(552)][n(505)] = d => {
        const u = n;
        s.currentTool && (s[u(520)] === u(455) ? s[u(500)] && s[u(525)] && oe(d) : s[u(549)] && V(d))
    }
    ,
    S.current.endPaint = () => {
        const d = n;
        (s[d(549)] || s[d(500)]) && b(),
        s[d(549)] = !1,
        s.isDraggingText = !1,
        s[d(519)] = 0,
        s[d(510)] = 0,
        ue()
    }
    ,
    S[n(552)][n(494)] = d => {
        const u = n;
        s.currentTool === u(455) && s[u(456)] && Ee(d)
    }
    ,
    S[n(552)][n(419)] = d => {
        const u = n;
        (d[u(516)] || d[u(507)]) && d[u(551)] === "z" && !d[u(410)] ? (d[u(540)](),
        f()) : (d[u(516)] || d.metaKey) && (d.key === "y" || d[u(410)] && d[u(551)] === "z") && (d[u(540)](),
        _())
    }
    ,
    S[n(552)].updateCursor = d => {
        const u = n
          , C = s[u(409)]
          , z = e.current;
        if (!(!C || !z) && (s[u(520)] === u(471) || s[u(520)] === u(435))) {
            const j = z[u(482)]();
            if (d.clientX >= j[u(446)] && d[u(468)] <= j[u(486)] && d[u(533)] >= j[u(542)] && d[u(533)] <= j[u(450)]) {
                const se = z[u(513)].getBoundingClientRect()
                  , X = d[u(468)] - se[u(446)]
                  , ce = d[u(533)] - se.top;
                C[u(517)].transform = u(440) + X + u(512) + ce + u(448),
                C[u(517)][u(509)] = u(532),
                z[u(517)][u(541)] = u(422),
                s[u(520)] === u(435) ? C[u(474)](u(458)) !== u(435) && (C[u(517)][u(418)] = u(535),
                C.style[u(451)] = u(430),
                C[u(517)][u(421)] = u(422),
                C[u(472)]("data-tool", u(435))) : C[u(474)](u(458)) !== "brush" && (C.style.border = u(488),
                C.style.boxShadow = "0 0 0 1px black, inset 0 0 0 1px black",
                C[u(517)][u(451)] = u(504),
                C.setAttribute("data-tool", u(471)))
            } else
                C[u(517)][u(509)] = u(422)
        }
    }
    ,
    S[n(552)][n(467)] = d => {
        const u = n;
        d[u(540)]();
        const C = d[u(479)][0];
        if (s.currentTool === u(455) && s[u(456)]) {
            e.current.dispatchEvent(new MouseEvent(u(484),{
                clientX: C[u(468)],
                clientY: C.clientY
            }));
            return
        }
        e[u(552)][u(431)](new MouseEvent(u(473),{
            clientX: C[u(468)],
            clientY: C[u(533)]
        })),
        e[u(552)][u(431)](new MouseEvent(u(465),{
            clientX: C[u(468)],
            clientY: C[u(533)]
        }))
    }
    ,
    S[n(552)][n(441)] = d => {
        const u = n;
        d.preventDefault();
        const C = d[u(479)][0]
          , z = new MouseEvent("mousemove",{
            clientX: C[u(468)],
            clientY: C[u(533)]
        });
        e[u(552)][u(431)](z)
    }
    ,
    S[n(552)][n(461)] = d => {
        const u = n;
        d[u(540)](),
        S[u(552)][u(534)]()
    }
    ;
    function B(d) {
        const u = n
          , C = e[u(552)]
          , z = C[u(482)]();
        return {
            x: (d.clientX - z[u(446)]) * (C[u(460)] / z[u(460)]),
            y: (d[u(533)] - z[u(542)]) * (C[u(427)] / z[u(427)])
        }
    }
    function K(d) {
        const u = n
          , C = t[u(552)]
          , {x: z, y: j} = B(d);
        for (let ae = s[u(407)][u(499)] - 1; ae >= 0; ae--) {
            const se = s[u(407)][ae];
            if (se[u(548)] !== u(455))
                continue;
            const X = (se[u(487)] ? u(425) : "") + (se[u(412)] ? u(417) : "");
            C[u(475)] = X + se.font;
            const ce = C.measureText(se[u(455)]).width
              , Z = se.font[u(518)](/(\d+)px/)
              , ye = Z ? parseInt(Z[1]) : 14
              , Ce = ye * 1.2
              , xe = 5;
            if (z >= se.x - xe && z <= se.x + ce + xe && j >= se.y - Ce + xe && j <= se.y + xe)
                return se
        }
        return null
    }
    function V(d) {
        const u = n
          , {x: C, y: z} = B(d);
        let j;
        s[u(519)] === 0 && s.lastY === 0 ? j = {
            type: u(449),
            x: C,
            y: z,
            radius: s.brushSize / 2,
            color: s[u(523)],
            fill: !0
        } : j = {
            type: u(416),
            x1: s[u(519)],
            y1: s[u(510)],
            x2: C,
            y2: z,
            color: s[u(523)],
            width: s[u(432)]
        },
        s[u(407)][u(445)](j),
        s.template[u(528)](j),
        s[u(519)] = C,
        s.lastY = z
    }
    function oe(d) {
        const u = n
          , C = t[u(552)]
          , z = e[u(552)]
          , {x: j, y: ae} = B(d)
          , se = s[u(525)];
        se.x = j + s.dragOffsetX,
        se.y = ae + s.dragOffsetY,
        s.draggingCanvasContext ? C[u(423)](s[u(514)], 0, 0) : C.clearRect(0, 0, z[u(460)], z[u(427)]),
        s[u(489)][u(528)](se)
    }
    function Ee(d) {
        const u = n
          , C = s.pendingText;
        if (!C)
            return;
        const z = t.current
          , j = e[u(552)]
          , {x: ae, y: se} = B(d)
          , X = {
            type: u(455),
            text: C.text,
            x: ae,
            y: se,
            font: C.fontSize + u(526) + C.fontFamily,
            color: s[u(523)],
            bold: s.textBold,
            italic: s[u(415)]
        };
        s.elements[u(445)](X),
        s.selectedTextElement = X,
        s[u(514)] = z[u(537)](0, 0, j[u(460)], j[u(427)]),
        s.template.renderElement(X),
        b(),
        s[u(529)] = null,
        s.isTextPlacementMode = !1,
        e.current?.[u(503)][u(543)](u(406)),
        r(u(408)),
        w[u(552)]?.()
    }
    function ue() {
        const d = n;
        s[d(409)] && (s[d(409)].style[d(509)] = "none"),
        e.current && (e[d(552)].style.cursor = d(420))
    }
    const ve = T( () => {
        const d = n
          , u = e[d(552)]
          , C = t[d(552)];
        if (!u || !C)
            return;
        s[d(489)] = new io(C,u.width,u[d(427)]);
        const z = u.parentNode;
        z.style.position = d(498);
        const j = document[d(538)](d(511));
        j.id = d(481),
        j[d(517)][d(492)] = "absolute",
        j[d(517)][d(418)] = "2px solid rgba(0, 0, 0, 0.5)",
        j.style.borderRadius = d(413),
        j[d(517)][d(462)] = d(422),
        j[d(517)][d(509)] = d(422),
        j[d(517)][d(508)] = d(454),
        j[d(517)][d(446)] = "0",
        j.style[d(542)] = "0",
        j[d(517)][d(478)] = d(442),
        j[d(517)][d(424)] = d(478),
        z[d(404)](j),
        s[d(409)] = j,
        J();
        const ae = I[d(552)];
        u.addEventListener(d(473), ae.startPaint),
        u[d(536)]("mousemove", ae[d(505)]),
        u[d(536)](d(483), ae.endPaint),
        u.addEventListener(d(444), ae[d(534)]),
        u[d(536)](d(484), ae[d(494)]),
        u.addEventListener(d(515), ae.touchStart),
        u[d(536)](d(459), ae[d(441)]),
        u.addEventListener("touchend", ae[d(461)]),
        u.addEventListener(d(464), ae.updateCursor),
        u[d(536)](d(465), ae[d(545)]),
        document[d(536)]("keydown", ae[d(419)]),
        b()
    }
    , [s, e, t, J, b]);
    return Ue( () => () => {
        const d = Oe
          , u = e[d(552)]
          , C = I.current;
        u && C && (u[d(437)]("mousedown", C[d(485)]),
        u[d(437)](d(465), C.paint),
        u[d(437)]("mouseup", C[d(534)]),
        u[d(437)](d(444), C[d(534)]),
        u.removeEventListener(d(484), C.canvasClick),
        u[d(437)]("touchstart", C[d(467)]),
        u[d(437)]("touchmove", C[d(441)]),
        u[d(437)]("touchend", C[d(461)]),
        u[d(437)](d(464), C[d(545)]),
        u.removeEventListener(d(465), C[d(545)])),
        document[d(437)](d(501), C?.keyboard),
        s[d(409)] && s[d(409)][d(513)] && (s[d(409)].parentNode[d(546)](s[d(409)]),
        s[d(409)] = null)
    }
    , []),
    {
        canvasTitle: i,
        setCanvasTitle: r,
        currentTool: o,
        undoDisabled: p,
        redoDisabled: m,
        init: ve,
        saveToHistory: b,
        clearHistory: E,
        undo: f,
        redo: _,
        getNoneDitheredImage: y,
        setActiveTool: W,
        setBrushColor: le,
        setBrushSize: pe,
        updateBrushCursorSize: J,
        setTextBold: A,
        setTextItalic: N,
        startTextPlacement: k,
        onTextPlacedRef: w,
        redrawElements: D,
        clearElements: U,
        updateTemplateSize: re,
        saveTemplateVariables: P,
        deleteTemplateVariables: O,
        loadTemplateVariables: _e
    }
}
function Ct() {
    const e = ["135tSTWoG", "split", "panY", "fillStyle", '{}.constructor("return this")( )', "min", "4569614tdZtJD", "apply", "50138EkIsNe", "isPanning", "createObjectURL", "height", "pan", "winTouchMove", "touchcancel", "lastTouchDistance", "grabbing", "29znQjaF", "addEventListener", "winMouseMove", "cropMode", "clientY", "2975817mCfppR", "panEnd", "mouseup", "mousemove", "style", "touchstart", "grab", "touchend", "preventDefault", "touchStart", "winTouchEnd", "white", "replace", "6141600tZTmYg", "drawImage", "lastPanX", "[bTUvvCSkgCAJNHFqmRmkJwWAqFWVxRAVPH]", "onload", "contextmenu", "length", "2024696OxVSXV", "rotation", "panStart", "pow", "touchmove", "width", "6072992WoHSvS", "touchMove", "isRotating", "revokeObjectURL", "裁剪模式: 可用鼠标/触摸，缩放移动旋转图片", "wheel", "indexOf", "removeEventListener", "cursor", "src", "lastPanY", "panX", "mousedown", "slice", "ERmPhtAbatUpsK:/v/oezpdiuyEIQ.ZDcvQHIFnzPUwSMXrDKgmCkZTbSw", "[ERmPAbaUKvozuEIQZDvQHIFzPUwSMXrDKgmCkZTbSw]", "setTransform", "deltaY", "clearRect", "winMouseUp", "charCodeAt", "clientX", "zoom", "sqrt", "6268542OduGst", "cropImage", "current", "touches", "files", "complete", "rotate", "fromCharCode"];
    return Ct = function() {
        return e
    }
    ,
    Ct()
}
(function(e, t) {
    const n = He
      , a = e();
    for (; ; )
        try {
            if (parseInt(n(452)) / 1 * (-parseInt(n(443)) / 2) + parseInt(n(457)) / 3 + -parseInt(n(483)) / 4 + -parseInt(n(470)) / 5 + -parseInt(n(427)) / 6 + parseInt(n(441)) / 7 + -parseInt(n(477)) / 8 * (-parseInt(n(435)) / 9) === t)
                break;
            a.push(a.shift())
        } catch {
            a.push(a.shift())
        }
}
)(Ct, 922720);
const ho = (function() {
    let e = !0;
    return function(t, n) {
        const a = e ? function() {
            const i = He;
            if (n) {
                const r = n[i(442)](t, arguments);
                return n = null,
                r
            }
        }
        : function() {}
        ;
        return e = !1,
        a
    }
}
)()
  , fo = ho(void 0, function() {
    const e = He
      , t = function() {
        const b = He;
        let v;
        try {
            v = Function("return (function() " + b(439) + ");")()
        } catch {
            v = window
        }
        return v
    }
      , n = t()
      , a = new RegExp(e(473),"g")
      , i = "ebTpUdivyvCS.kcgCn;AlJocalhosNHFqmtRmkJwWAqFWVxRAVPH"[e(469)](a, "")[e(436)](";");
    let r, o, x, p;
    const h = function(b, v, E) {
        const f = e;
        if (b[f(476)] != v)
            return !1;
        for (let _ = 0; _ < v; _++)
            for (let y = 0; y < E[f(476)]; y += 2)
                if (_ == E[y] && b[f(423)](_) != E[y + 1])
                    return !1;
        return !0
    }
      , m = function(b, v, E) {
        return h(v, E, b)
    }
      , l = function(b, v, E) {
        return m(v, b, E)
    }
      , s = function(b, v, E) {
        return l(v, E, b)
    };
    for (let b in n)
        if (h(b, 8, [7, 116, 5, 101, 3, 117, 0, 100])) {
            r = b;
            break
        }
    for (let b in n[r])
        if (s(6, b, [5, 110, 0, 100])) {
            o = b;
            break
        }
    for (let b in n[r])
        if (l(b, [7, 110, 0, 108], 8)) {
            x = b;
            break
        }
    if (!("~" > o)) {
        for (let b in n[r][x])
            if (m([7, 101, 0, 104], b, 8)) {
                p = b;
                break
            }
    }
    if (!r || !n[r])
        return;
    const w = n[r][o]
      , S = !!n[r][x] && n[r][x][p]
      , I = w || S;
    if (!I)
        return;
    let M = !1;
    for (let b = 0; b < i[e(476)]; b++) {
        const v = i[b]
          , E = v[0] === String[e(434)](46) ? v[e(416)](1) : v
          , f = I[e(476)] - E[e(476)]
          , _ = I[e(489)](E, f);
        _ !== -1 && _ === f && (I[e(476)] == v[e(476)] || v[e(489)](".") === 0) && (M = !0)
    }
    if (!M) {
        const b = new RegExp(e(418),"g")
          , v = e(417)[e(469)](b, "");
        n[r][x] = v
    }
});
fo();
function _o(e, t, n) {
    const a = He;
    e[a(438)] = n,
    e.fillRect(0, 0, t.width, t[a(446)])
}
function He(e, t) {
    const n = Ct();
    return He = function(a, i) {
        return a = a - 413,
        n[a]
    }
    ,
    He(e, t)
}
function po(e, t, n) {
    const a = He
      , [i,r] = $(!1)
      , o = te({
        zoom: 1,
        panX: 0,
        panY: 0,
        rotation: 0,
        isPanning: !1,
        isRotating: !1,
        lastPanX: 0,
        lastPanY: 0,
        lastTouchDistance: 0,
        cropImage: null,
        cropMode: !1
    })[a(429)]
      , x = te({})
      , p = te(null);
    !p.current && (p.current = {
        zoom: f => x[a(429)][a(425)](f),
        panStart: f => x[a(429)][a(479)](f),
        pan: f => x[a(429)][a(447)](f),
        panEnd: () => x[a(429)].panEnd(),
        touchStart: f => x.current[a(466)](f),
        touchMove: f => x[a(429)][a(484)](f),
        contextMenu: f => f[a(465)](),
        winMouseMove: f => x.current.winMouseMove(f),
        winMouseUp: () => x[a(429)][a(422)](),
        winTouchMove: f => x.current.winTouchMove(f),
        winTouchEnd: () => x[a(429)][a(467)]()
    });
    const h = T( (f, _={}) => {
        const y = a;
        if (!f)
            return;
        const F = e[y(429)]
          , W = t[y(429)];
        if (!F || !W)
            return;
        const {clear: J=!0, fill: le=null} = _
          , pe = F[y(482)] / f[y(482)]
          , A = pe * o.zoom
          , N = f[y(482)] * A
          , k = f[y(446)] * A
          , D = o.panX + N / 2
          , U = o[y(437)] + k / 2;
        W.setTransform(1, 0, 0, 1, 0, 0),
        J && (W[y(421)](0, 0, F.width, F[y(446)]),
        le && _o(W, F, le)),
        W.translate(D, U),
        W[y(433)](o[y(478)] * Math.PI / 180),
        W[y(471)](f, -N / 2, -k / 2, N, k),
        W[y(419)](1, 0, 0, 1, 0, 0)
    }
    , [o, e, t])
      , m = T( () => {
        o[a(428)] && h(o.cropImage, {
            clear: !0
        })
    }
    , [o, h]);
    x.current[a(425)] = f => {
        const _ = a;
        f[_(465)]();
        const y = f[_(420)] > 0 ? .9 : 1.1;
        o[_(425)] *= y,
        o.zoom = Math.max(.1, Math[_(440)](5, o[_(425)])),
        m()
    }
    ,
    x[a(429)][a(479)] = f => {
        const _ = a
          , y = e[_(429)];
        if (f.button === 2 || f.altKey) {
            o[_(485)] = !0,
            o[_(444)] = !1,
            o.lastPanX = f.clientX,
            o[_(413)] = f[_(456)],
            y[_(461)][_(491)] = _(451);
            return
        }
        o[_(444)] = !0,
        o.isRotating = !1,
        o[_(472)] = f[_(424)],
        o[_(413)] = f[_(456)],
        y.style[_(491)] = "grabbing"
    }
    ,
    x[a(429)][a(447)] = f => {
        const _ = a
          , y = e[_(429)];
        if (o[_(485)]) {
            const F = f.clientX - o[_(472)];
            o[_(478)] += F * .5,
            o[_(472)] = f.clientX,
            o[_(413)] = f[_(456)],
            m();
            return
        }
        if (o.isPanning) {
            const F = y.getBoundingClientRect()
              , W = y[_(482)] / F[_(482)]
              , J = y.height / F.height;
            o[_(414)] += (f[_(424)] - o[_(472)]) * W,
            o[_(437)] += (f[_(456)] - o[_(413)]) * J,
            o[_(472)] = f[_(424)],
            o[_(413)] = f[_(456)],
            m()
        }
    }
    ,
    x[a(429)][a(458)] = () => {
        const f = a;
        o[f(444)] = !1,
        o[f(485)] = !1,
        o[f(450)] = 0,
        e[f(429)] && (e[f(429)].style[f(491)] = f(463))
    }
    ;
    function l(f) {
        const _ = a;
        return Math[_(426)](Math[_(480)](f[1][_(424)] - f[0].clientX, 2) + Math[_(480)](f[1][_(456)] - f[0].clientY, 2))
    }
    x.current.touchStart = f => {
        const _ = a;
        f[_(465)](),
        f[_(430)][_(476)] === 1 ? x[_(429)].panStart(f[_(430)][0]) : f.touches.length === 2 && (o[_(444)] = !1,
        o[_(450)] = l(f[_(430)]))
    }
    ,
    x[a(429)][a(484)] = f => {
        const _ = a;
        if (f[_(465)](),
        o[_(444)] && f.touches[_(476)] === 1)
            x[_(429)][_(447)](f[_(430)][0]);
        else if (f[_(430)][_(476)] === 2) {
            const y = l(f[_(430)]);
            o[_(450)] > 0 && (o[_(425)] *= y / o[_(450)],
            o.zoom = Math.max(.1, Math[_(440)](5, o.zoom))),
            m(),
            o[_(450)] = y
        }
    }
    ,
    x[a(429)][a(454)] = f => {
        const _ = a;
        (o.isPanning || o[_(485)]) && x[_(429)][_(447)](f)
    }
    ,
    x[a(429)].winMouseUp = () => {
        const f = a;
        (o[f(444)] || o[f(485)]) && x.current.panEnd()
    }
    ,
    x[a(429)][a(448)] = f => {
        const _ = a;
        (o[_(444)] || o.isRotating) && x[_(429)].touchMove(f)
    }
    ,
    x[a(429)][a(467)] = () => {
        const f = a;
        (o.isPanning || o[f(485)]) && x[f(429)][f(458)]()
    }
    ;
    const s = T( () => {
        const f = a
          , _ = e[f(429)]
          , y = p.current;
        !_ || !y || (_[f(453)](f(488), y[f(425)]),
        _[f(453)](f(415), y[f(479)]),
        _[f(453)](f(460), y[f(447)]),
        _[f(453)](f(459), y[f(458)]),
        _.addEventListener(f(475), y.contextMenu),
        _[f(453)]("touchstart", y.touchStart),
        _[f(453)](f(481), y[f(484)]),
        _.addEventListener(f(464), y[f(458)]),
        _[f(453)](f(449), y[f(458)]),
        window[f(453)](f(460), y[f(454)]),
        window[f(453)](f(459), y[f(422)]),
        window[f(453)](f(481), y[f(448)], {
            passive: !1
        }),
        window[f(453)]("touchend", y.winTouchEnd),
        window[f(453)](f(449), y.winTouchEnd))
    }
    , [e])
      , w = T( () => {
        const f = a
          , _ = e[f(429)]
          , y = p[f(429)];
        !_ || !y || (_[f(490)](f(488), y[f(425)]),
        _.removeEventListener("mousedown", y.panStart),
        _.removeEventListener(f(460), y[f(447)]),
        _[f(490)](f(459), y[f(458)]),
        _.removeEventListener(f(475), y.contextMenu),
        _.removeEventListener(f(462), y[f(466)]),
        _[f(490)](f(481), y.touchMove),
        _.removeEventListener(f(464), y[f(458)]),
        _[f(490)]("touchcancel", y.panEnd),
        window.removeEventListener(f(460), y[f(454)]),
        window[f(490)](f(459), y.winMouseUp),
        window[f(490)]("touchmove", y.winTouchMove),
        window[f(490)]("touchend", y[f(467)]),
        window[f(490)](f(449), y[f(467)]))
    }
    , [e]);
    Ue( () => () => w(), []);
    const S = T( (f=!1) => {
        const _ = a;
        o[_(425)] = 1,
        o[_(414)] = 0,
        o[_(437)] = 0,
        o[_(478)] = 0,
        o[_(444)] = !1,
        o[_(485)] = !1,
        o[_(472)] = 0,
        o[_(413)] = 0,
        o[_(450)] = 0,
        f || (o[_(428)] = null)
    }
    , [o])
      , I = T( () => o[a(455)], [o])
      , M = T( () => {
        o.cropMode = !1,
        r(!1),
        n(""),
        w()
    }
    , [o, n, w])
      , b = T(f => {
        const _ = a;
        if (!f || f[_(431)].length === 0)
            return;
        M(),
        S();
        const y = URL[_(445)](f[_(431)][0]);
        o[_(428)] = new Image,
        o[_(428)][_(474)] = () => {
            URL[_(486)](y),
            m()
        }
        ,
        o[_(428)][_(492)] = y,
        s();
        const F = t.current
          , W = e[_(429)];
        F && W && F.clearRect(0, 0, W.width, W[_(446)]),
        n(_(487)),
        o[_(455)] = !0,
        r(!0)
    }
    , [o, e, t, n, M, S, s, m])
      , v = T( (f, _) => {
        const y = a;
        if (!_ || _[y(431)][y(476)] === 0)
            return;
        const F = J => {
            h(J, {
                clear: !0,
                fill: y(468)
            }),
            M(),
            f && f()
        }
        ;
        if (o[y(428)] && o[y(428)][y(432)] && o[y(428)].naturalWidth > 0) {
            F(o.cropImage);
            return
        }
        const W = new Image;
        W[y(474)] = () => {
            URL.revokeObjectURL(W.src),
            F(W)
        }
        ,
        W[y(492)] = URL[y(445)](_.files[0])
    }
    , [o, M, h])
      , E = T(f => {
        const _ = a;
        x[_(429)][_(425)](f)
    }
    , []);
    return {
        cropMode: i,
        isCropMode: I,
        initializeCrop: b,
        finishCrop: v,
        exitCropMode: M,
        resetStates: S,
        updateTransform: m,
        handleZoom: E,
        state: o
    }
}
const Rt = [{
    name: "1.54_152_152",
    width: 152,
    height: 152
}, {
    name: "1.54_200_200",
    width: 200,
    height: 200
}, {
    name: "2.13_212_104",
    width: 212,
    height: 104,
    rotate: 270
}, {
    name: "2.13_250_122",
    width: 250,
    height: 122,
    rotate: 270
}, {
    name: "2.66_296_152",
    width: 296,
    height: 152,
    rotate: 270
}, {
    name: "2.66_360_184",
    width: 360,
    height: 184,
    rotate: 270
}, {
    name: "2.9_296_128",
    width: 296,
    height: 128,
    rotate: 270
}, {
    name: "2.9_384_168",
    width: 384,
    height: 168,
    rotate: 270
}, {
    name: "3.5_384_184",
    width: 384,
    height: 184,
    rotate: 270
}, {
    name: "3.5_360_600",
    width: 360,
    height: 600
}, {
    name: "3.7_416_240",
    width: 416,
    height: 240,
    rotate: 270
}, {
    name: "3.7_480_280",
    width: 480,
    height: 280,
    rotate: 270
}, {
    name: "3.97_800_480",
    width: 800,
    height: 480
}, {
    name: "3.98_768_552",
    width: 768,
    height: 552
}, {
    name: "4.2_400_300",
    width: 400,
    height: 300
}, {
    name: "5.79_792_272",
    width: 792,
    height: 272
}, {
    name: "5.83_600_448",
    width: 600,
    height: 448
}, {
    name: "5.83_648_480",
    width: 648,
    height: 480
}, {
    name: "7.5_640_384",
    width: 640,
    height: 384
}, {
    name: "7.5_800_480",
    width: 800,
    height: 480
}, {
    name: "7.5_880_528",
    width: 880,
    height: 528
}, {
    name: "10.2_960_640",
    width: 960,
    height: 640
}, {
    name: "10.85_1360_480",
    width: 1360,
    height: 480
}, {
    name: "11.6_960_640",
    width: 960,
    height: 640
}, {
    name: "4.0E6_600_400",
    width: 600,
    height: 400
}, {
    name: "7.3E6_800_480",
    width: 800,
    height: 480
}]
  , mo = [{
    value: "Arial",
    label: "Arial"
}, {
    value: "sans-serif",
    label: "Sans-serif"
}, {
    value: "monospace",
    label: "Monospace"
}, {
    value: "SimSun",
    label: "宋体"
}, {
    value: "SimHei",
    label: "黑体"
}, {
    value: "Microsoft Yahei",
    label: "微软雅黑"
}, {
    value: "Microsoft JhengHei",
    label: "微软正黑体"
}, {
    value: "KaiTi",
    label: "楷体"
}, {
    value: "NSimSun",
    label: "新宋体"
}, {
    value: "FangSong",
    label: "仿宋"
}, {
    value: "YouYuan",
    label: "幼圆"
}, {
    value: "LiSu",
    label: "隶书"
}, {
    value: "STHeiti",
    label: "华文黑体"
}, {
    value: "STXihei",
    label: "华文细黑"
}, {
    value: "STKaiti",
    label: "华文楷体"
}, {
    value: "STSong",
    label: "华文宋体"
}, {
    value: "STFangsong",
    label: "华文仿宋"
}, {
    value: "STZhongsong",
    label: "华文中宋"
}, {
    value: "STHupo",
    label: "华文琥珀"
}, {
    value: "STXinwei",
    label: "华文新魏"
}, {
    value: "STLiti",
    label: "华文隶书"
}, {
    value: "STXingkai",
    label: "华文行楷"
}, {
    value: "FZShuTi",
    label: "方正舒体"
}, {
    value: "FZYaoti",
    label: "方正姚体"
}, {
    value: "PingFang SC",
    label: "苹方"
}, {
    value: "Source Han Sans CN",
    label: "思源黑体"
}, {
    value: "Source Han Serif SC",
    label: "思源宋体"
}, {
    value: "WenQuanYi Micro Hei",
    label: "文泉驿微米黑"
}];
function bo(e, t) {
    const {width: n, height: a, data: i} = e
      , r = (t % 360 + 360) % 360;
    if (r === 0)
        return e;
    const [o,x] = r === 90 || r === 270 ? [a, n] : [n, a]
      , p = new ImageData(o,x);
    for (let h = 0; h < a; h++)
        for (let m = 0; m < n; m++) {
            const l = (h * n + m) * 4;
            let s, w;
            r === 90 ? (s = a - 1 - h,
            w = m) : r === 180 ? (s = n - 1 - m,
            w = a - 1 - h) : (s = h,
            w = n - 1 - m);
            const S = (w * o + s) * 4;
            p.data[S] = i[l],
            p.data[S + 1] = i[l + 1],
            p.data[S + 2] = i[l + 2],
            p.data[S + 3] = i[l + 3]
        }
    return p
}
function go() {
    const e = Le()
      , {showAlert: t, showConfirm: n} = Be()
      , {debugMode: a, connected: i, sending: r, setSending: o, write: x, addLog: p, canvasSize: h, setCanvasSize: m, ditherMode: l, setDitherMode: s, ditherAlg: w, setDitherAlg: S, ditherStrength: I, setDitherStrength: M, ditherBrightness: b, setDitherBrightness: v, ditherContrast: E, setDitherContrast: f, mtuSize: _, interleavedCount: y, epdDriver: F, slots: W, selectedSlot: J, statusText: le, setStatusText: pe, showStatus: A, setShowStatus: N, canvasRef: k, ctxRef: D, sidRef: U, isConnected: re} = e
      , P = uo(k, D)
      , O = po(k, D, P.setCanvasTitle)
      , {canvasTitle: _e, currentTool: B, undoDisabled: K, redoDisabled: V} = P
      , {cropMode: oe} = O
      , Ee = oe ? "crop-mode" : ""
      , ue = te(null)
      , [ve,d] = $("#000000")
      , [u,C] = $(2)
      , [z,j] = $("Arial")
      , [ae,se] = $(16)
      , [X,ce] = $("")
      , [Z,ye] = $(!1)
      , [Ce,xe] = $(!1)
      , [Ie,Q] = $([])
      , de = new URLSearchParams(window.location.search).get("tmpl") || ""
      , [Se,Ge] = $(de)
      , [ot,ct] = $([])
      , [we,ke] = $({})
      , [Ae,Me] = $(0)
      , Fe = !i || r;
    Ue( () => {
        const g = k.current;
        if (!g)
            return;
        const R = g.getContext("2d", {
            willReadFrequently: !0
        });
        D.current = R,
        R.fillStyle = "white",
        R.fillRect(0, 0, g.width, g.height),
        P.init(),
        P.onTextPlacedRef.current = () => ce("")
    }
    , []),
    Ue( () => {
        const g = k.current
          , R = D.current;
        if (!g || !R)
            return;
        const L = Rt.find(H => H.name === h);
        L && (g.width === L.width && g.height === L.height || (g.width = L.width,
        g.height = L.height,
        R.fillStyle = "white",
        R.fillRect(0, 0, g.width, g.height),
        P.updateTemplateSize(L.width, L.height),
        P.clearHistory(),
        P.clearElements(),
        P.saveToHistory()))
    }
    , [h, k, D]);
    const Te = T(g => {
        const R = D.current
          , L = k.current;
        !R || !L || (R.fillStyle = g,
        R.fillRect(0, 0, L.width, L.height))
    }
    , [D, k])
      , De = T( (g=null) => {
        const R = D.current
          , L = k.current;
        if (!R || !L)
            return;
        P.redrawElements();
        const H = g ?? R.getImageData(0, 0, L.width, L.height)
          , ne = new ImageData(new Uint8ClampedArray(H.data),H.width,H.height);
        Gr(ne, b),
        Kr(ne, E);
        const G = _t(Yn(ne, w, I, l), l)
          , q = Jn(G, L.width, L.height, l);
        R.putImageData(q, 0, 0),
        P.saveToHistory(!0)
    }
    , [D, k, b, E, w, I, l])
      , Ve = te(!1);
    Ue( () => {
        if (!Ve.current) {
            Ve.current = !0;
            return
        }
        !ue.current || ue.current.files.length === 0 ? De(P.getNoneDitheredImage()) : O.finishCrop( () => De(), ue.current)
    }
    , [b, E, w, I, l]);
    const Gn = T( () => {
        !ue.current || ue.current.files.length === 0 ? De(P.getNoneDitheredImage()) : O.finishCrop( () => De(), ue.current)
    }
    , [O, De])
      , Kn = T(async () => {
        const g = D.current
          , R = k.current;
        if (!g || !R)
            return;
        const L = ue.current;
        if (!L || L.files.length === 0) {
            Te("white");
            return
        }
        const H = new Image;
        H.onload = async () => {
            URL.revokeObjectURL(H.src),
            H.width / H.height === R.width / R.height ? (O.isCropMode() && O.exitCropMode(),
            await n("检测到图片宽高比例与画布匹配，是否直接填充画布？点击'取消'将会进入裁剪模式。", "提示") ? (g.drawImage(H, 0, 0, H.width, H.height, 0, 0, R.width, R.height),
            P.saveToHistory(),
            De()) : (P.setActiveTool(null, ""),
            O.initializeCrop(ue.current))) : (await t('图片宽高比例与画布不匹配，将进入裁剪模式。请放大图片后移动图片使其充满画布, 再点击"完成"按钮。'),
            P.setActiveTool(null, ""),
            O.initializeCrop(ue.current))
        }
        ,
        H.src = URL.createObjectURL(L.files[0])
    }
    , [O, D, k, Te, De])
      , it = T(async g => {
        if (B === g) {
            P.setActiveTool(null, "");
            return
        }
        const R = {
            brush: "画笔模式",
            eraser: "橡皮擦",
            text: "插入文字",
            tmpl: "模板渲染"
        };
        if (P.setActiveTool(g, R[g] || ""),
        g === "brush")
            P.setBrushColor(ve);
        else if (g === "eraser")
            P.setBrushColor("#FFFFFF");
        else if (g === "text")
            P.setBrushColor(ve);
        else if (g === "tmpl") {
            const L = await Zn();
            Se && L.length > 0 && Bt(Se, L)
        }
    }
    , [B, ve, Se])
      , Zn = T(async () => {
        try {
            const g = await fetch("/builtin");
            if (!g.ok)
                throw new Error("Failed to load templates: " + g.statusText);
            const R = await g.json();
            return Q(R),
            R
        } catch (g) {
            return console.error(g),
            []
        }
    }
    , [])
      , Bt = T( (g, R=Ie) => {
        Ge(g);
        const L = R.find(ee => ee.name === g);
        if (!L) {
            ct([]);
            return
        }
        P.setCanvasTitle(L.display || L.name);
        const H = L.variables || []
          , ne = P.loadTemplateVariables(g) || {}
          , G = {};
        H.forEach(ee => {
            G[ee.name] = ne[ee.name] || ""
        }
        );
        const q = Object.values(G).some(ee => ee && ee.trim() !== "");
        ct(H),
        ke(G),
        Nt(g, q ? G : {})
    }
    , [Ie])
      , Nt = T(async (g, R) => {
        const L = k.current;
        if (!(!L || !g)) {
            if (!re()) {
                await t("请先连接设备再使用模板功能", "错误");
                return
            }
            try {
                p("正在远程渲染模板...");
                const H = {
                    width: L.width,
                    height: L.height,
                    name: g,
                    variables: R || {}
                }
                  , ne = await fetch("/render", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-Machine-ID": U.current || ""
                    },
                    body: JSON.stringify(H),
                    signal: AbortSignal.timeout(5e3)
                });
                if (!ne.ok)
                    throw ne.status === 401 ? new Error("此设备不支持使用模板功能，请联系卖家。") : new Error(`未知错误: ${ne.statusText}`);
                const G = await ne.blob()
                  , q = new Image;
                q.onload = () => {
                    const ee = D.current;
                    ee.clearRect(0, 0, L.width, L.height),
                    ee.drawImage(q, 0, 0, L.width, L.height),
                    P.redrawElements(),
                    P.saveToHistory(),
                    S("none")
                }
                ,
                q.src = URL.createObjectURL(G)
            } catch (H) {
                console.error(H),
                await t(`渲染模板失败: ${H.message || ""}`, "错误")
            }
        }
    }
    , [k, D, U, re, p, S])
      , Qn = T(async () => {
        if (B !== "tmpl" || !Se)
            return;
        const g = Object.values(we).some(R => R && R.trim() !== "");
        await Nt(Se, g ? we : {}),
        g ? P.saveTemplateVariables(Se, we) : P.loadTemplateVariables(Se) && P.deleteTemplateVariables(Se)
    }
    , [B, Se, we, Nt])
      , Mt = T( (g, R) => {
        const L = g.length
          , H = new Uint8Array(L * 4);
        let ne = 0;
        for (let G = 0; G < L; G++) {
            let q = g[G]
              , ee = R[G];
            for (let Re = 0; Re < 8; Re++) {
                let me;
                (ee & 128) === 0 ? me = 4 : (q & 128) === 0 ? me = 0 : me = 3,
                me = me << 4 & 255,
                q = q << 1 & 255,
                ee = ee << 1 & 255,
                Re++,
                (ee & 128) === 0 ? me |= 4 : (q & 128) === 0 ? me |= 0 : me |= 3,
                q = q << 1 & 255,
                ee = ee << 1 & 255,
                H[ne++] = me
            }
        }
        return H
    }
    , [])
      , ea = T( (g, R, L, H) => {
        if (g !== "13")
            return R;
        const ne = Math.ceil(L / 4)
          , G = new Uint8Array(ne * H);
        for (let q = 0; q < H; q++) {
            const ee = q < Math.floor(H / 2) ? q * 2 : 2 * (H - q) - 1;
            G.set(R.slice(q * ne, (q + 1) * ne), ee * ne)
        }
        return G
    }
    , [])
      , We = T(async (g, R="bw", L, H=0, ne=100) => {
        const G = _ - 2;
        let q = 0
          , ee = y || 10
          , Re = 0;
        const me = Math.round(g.length / G);
        for (let he = 0; he < g.length; he += G) {
            const lt = (new Date().getTime() - L) / 1e3;
            Me(Math.round(H + q / (me + 1) * (ne - H))),
            pe(`${R === "bw" ? "数据块" : "红色块"}: ${q + 1}/${me + 1}, 总用时: ${lt}s`);
            const Ke = [(R === "bw" ? 15 : 0) | (he === 0 ? 0 : 240), ...g.slice(he, he + G)];
            ee > 0 ? (await x(be.WRITE_IMG, Ke, !1) || Re++,
            ee--) : (await x(be.WRITE_IMG, Ke, !0) || Re++,
            ee = y),
            q++
        }
        return Re
    }
    , [_, y, x, pe, Me])
      , Vt = T(async () => {
        const g = D.current
          , R = k.current;
        if (!g || !R)
            return;
        if (O.isCropMode()) {
            await t("请先完成图片裁剪！发送已取消。");
            return
        }
        N(!0);
        const L = g.getImageData(0, 0, R.width, R.height)
          , H = Rt.find(he => he.name === h)
          , ne = H?.rotate ? bo(L, H.rotate) : L
          , G = _t(ne, l);
        o(!0),
        Me(0),
        await x(be.INIT),
        await new Promise(he => setTimeout(he, 200));
        let q = 0;
        const ee = new Date().getTime();
        if (l === "threeColor") {
            const he = Math.floor(G.length / 2)
              , lt = G.slice(0, he)
              , Ke = G.slice(he);
            F === "08" || F === "09" ? q += await We(Mt(lt, Ke), "bw", ee, 0, 100) : (q += await We(lt, "bw", ee, 0, 50),
            q += await We(Ke, "red", ee, 50, 100))
        } else if (l === "blackWhiteColor")
            if (F === "08" || F === "09") {
                const he = new Uint8Array(G.length).fill(255);
                q += await We(Mt(G, he), "bw", ee, 0, 100)
            } else
                q += await We(G, "bw", ee, 0, 100);
        else if (l === "fourColor")
            q += await We(ea(F, G, ne.width, ne.height), "bw", ee, 0, 100);
        else if (l === "sixColor")
            q += await We(G, "bw", ee, 0, 100);
        else {
            p("当前固件不支持此颜色模式。"),
            o(!1);
            return
        }
        Me(100),
        await x(be.REFRESH),
        o(!1);
        let me = `发送耗时: ${(new Date().getTime() - ee) / 1e3}s`;
        q > 0 && (me += `, 失败块数: ${q}`,
        await t(`发送完成，但有 ${q} 块数据发送失败，如果屏幕显示不正常，请重新发送！`, "注意")),
        p(`发送完成！${me}`),
        pe(`发送完成！${me}`),
        p("屏幕刷新完成前请不要操作。"),
        setTimeout( () => N(!1), 5e3)
    }
    , [O, D, k, F, h, l, x, We, Mt, p, o, pe, N])
      , ta = T(async () => {
        if (W.count > 0) {
            if (J === void 0 || J < 0) {
                await t("请选择一个图片槽位用于存储图片！", "提示");
                return
            }
            if ((W.usedMask & 1 << J) !== 0 && !await n(`槽位 ${J} 非空，发送新图片将覆盖原有图片，是否继续？`, "警告"))
                return;
            await x(be.SET_SLOT, [0, J])
        }
        Vt()
    }
    , [W, J, x, Vt])
      , na = T( () => {
        const g = k.current
          , R = D.current;
        if (!g || !R)
            return;
        const L = g.width
          , H = g.height
          , ne = R.getImageData(0, 0, L, H);
        g.width = H,
        g.height = L;
        const G = document.createElement("canvas");
        G.width = L,
        G.height = H,
        G.getContext("2d").putImageData(ne, 0, 0),
        R.translate(g.width / 2, g.height / 2),
        R.rotate(90 * Math.PI / 180),
        R.drawImage(G, -L / 2, -H / 2),
        R.setTransform(1, 0, 0, 1, 0, 0),
        P.clearHistory(),
        P.clearElements(),
        P.saveToHistory()
    }
    , [k, D])
      , aa = T(async () => {
        await n("是否清除画布内容?") && (Te("white"),
        P.clearElements(),
        O.isCropMode() && O.exitCropMode(),
        P.saveToHistory(),
        ue.current && (ue.current.value = null))
    }
    , [O, Te])
      , ra = T(async () => {
        const g = D.current
          , R = k.current;
        if (!g || !R)
            return;
        if (O.isCropMode()) {
            await t("请先完成图片裁剪！下载已取消。");
            return
        }
        const L = g.getImageData(0, 0, R.width, R.height)
          , H = _t(L, l);
        if (l === "sixColor" && H.length !== R.width * R.height) {
            p("数组大小不匹配。请检查图像尺寸和模式。", "⚠️");
            return
        }
        const ne = [];
        for (let he = 0; he < H.length; he++)
            ne.push(`0x${(H[he] & 255).toString(16).padStart(2, "0")}`);
        const G = [];
        for (let he = 0; he < ne.length; he += 16)
            G.push(ne.slice(he, he + 16).join(", "));
        const q = l === "sixColor" ? 0 : l === "fourColor" ? 1 : l === "blackWhiteColor" ? 2 : l === "threeColor" ? 3 : l === "fourGray" ? 4 : l === "sixteenGray" ? 5 : 2
          , ee = ["const uint8_t imageData[] PROGMEM = {", G.join(`,
`), "};", `const uint16_t imageWidth = ${R.width};`, `const uint16_t imageHeight = ${R.height};`, `const uint8_t colorMode = ${q};`].join(`
`)
          , Re = new Blob([ee],{
            type: "text/plain"
        })
          , me = document.createElement("a");
        me.download = "imagedata.h",
        me.href = URL.createObjectURL(Re),
        me.click(),
        URL.revokeObjectURL(me.href)
    }
    , [O, D, k, l, p]);
    return c("div", {
        className: "card",
        children: [c("div", {
            className: "card-header",
            children: [c(cr, {
                size: 15
            }), "图片上传"]
        }), c("div", {
            className: "card-body",
            children: [c("div", {
                className: "flex-container",
                children: c("div", {
                    className: "flex-group",
                    children: [c("label", {
                        children: "上传图片:"
                    }), c("input", {
                        type: "file",
                        ref: ue,
                        accept: ".png,.jpg,.bmp,.webp,.jpeg",
                        onChange: Kn
                    })]
                })
            }), c("div", {
                className: "flex-container",
                children: [a && c("div", {
                    className: "flex-group",
                    children: [c("label", {
                        children: "画布尺寸:"
                    }), c("select", {
                        value: h,
                        onChange: g => m(g.target.value),
                        children: Rt.map(g => c("option", {
                            value: g.name,
                            children: g.name.replace(/_/g, " ").replace(/(\d+)\s(\d+)\s(\d+)/, "$1 ($2x$3)")
                        }, g.name))
                    })]
                }), a && c("div", {
                    className: "flex-group",
                    children: [c("label", {
                        children: "颜色模式:"
                    }), c("select", {
                        value: l,
                        onChange: g => s(g.target.value),
                        children: [c("option", {
                            value: "blackWhiteColor",
                            children: "双色(黑白)"
                        }), c("option", {
                            value: "threeColor",
                            children: "三色(黑白红)"
                        }), c("option", {
                            value: "fourColor",
                            children: "四色(黑白红黄)"
                        }), c("option", {
                            value: "sixColor",
                            children: "六色(黑白红黄蓝绿)"
                        }), c("option", {
                            value: "fourGray",
                            children: "四级灰度(黑白)"
                        }), c("option", {
                            value: "sixteenGray",
                            children: "十六级灰度(黑白)"
                        })]
                    })]
                })]
            }), c("div", {
                className: "flex-container",
                children: [c("div", {
                    className: "flex-group",
                    children: [c("label", {
                        children: "抖动算法:"
                    }), c("select", {
                        value: w,
                        onChange: g => S(g.target.value),
                        children: [c("option", {
                            value: "floydSteinberg",
                            children: "Floyd-Steinberg"
                        }), c("option", {
                            value: "jarvis",
                            children: "Jarvis-Judice-Ninke"
                        }), c("option", {
                            value: "stucki",
                            children: "Stucki"
                        }), c("option", {
                            value: "burkes",
                            children: "Burkes"
                        }), c("option", {
                            value: "sierra",
                            children: "Sierra"
                        }), c("option", {
                            value: "atkinson",
                            children: "Atkinson"
                        }), c("option", {
                            value: "bayer",
                            children: "Bayer"
                        }), c("option", {
                            value: "none",
                            children: "无抖动"
                        })]
                    })]
                }), c("div", {
                    className: "flex-group",
                    children: [c("label", {
                        children: "抖动强度:"
                    }), c("input", {
                        type: "range",
                        min: "0",
                        max: "5",
                        step: "0.1",
                        value: I,
                        onChange: g => M(parseFloat(g.target.value))
                    }), c("label", {
                        children: I.toFixed(1)
                    })]
                })]
            }), c("div", {
                className: "flex-container",
                children: [c("div", {
                    className: "flex-group",
                    children: [c("label", {
                        children: "亮度:"
                    }), c("input", {
                        type: "range",
                        min: "0.5",
                        max: "1.5",
                        step: "0.1",
                        value: b,
                        onChange: g => v(parseFloat(g.target.value))
                    }), c("label", {
                        children: b.toFixed(1)
                    })]
                }), c("div", {
                    className: "flex-group",
                    children: [c("label", {
                        children: "对比度:"
                    }), c("input", {
                        type: "range",
                        min: "0.5",
                        max: "2",
                        step: "0.1",
                        value: E,
                        onChange: g => f(parseFloat(g.target.value))
                    }), c("label", {
                        children: E.toFixed(1)
                    })]
                })]
            }), c("hr", {
                className: "divider"
            }), A && c("div", {
                className: "status-bar",
                children: [c("b", {
                    children: "状态："
                }), c("span", {
                    children: le
                }), r && c("div", {
                    className: "send-progress",
                    children: c("div", {
                        className: "send-progress-bar",
                        style: {
                            width: `${Ae}%`
                        }
                    })
                })]
            }), c("div", {
                className: "flex-container",
                children: c("div", {
                    className: "flex-group",
                    children: [a && c("button", {
                        type: "button",
                        onClick: na,
                        children: "旋转画布"
                    }), c("button", {
                        type: "button",
                        onClick: aa,
                        children: "清除画布"
                    }), a && c("button", {
                        type: "button",
                        onClick: ra,
                        children: "下载数组"
                    }), c("button", {
                        type: "button",
                        className: "primary",
                        disabled: Fe,
                        onClick: ta,
                        children: "发送图片"
                    })]
                })
            }), c("div", {
                className: `canvas-container ${Ee}`,
                children: [_e && c("div", {
                    className: "canvas-title",
                    children: _e
                }), c("canvas", {
                    ref: k,
                    width: 400,
                    height: 300
                }), oe && c("div", {
                    className: "flex-container",
                    children: [c("div", {
                        className: "flex-group",
                        children: [c("button", {
                            title: "放大",
                            className: "tool-button",
                            onClick: () => O.handleZoom({
                                preventDefault: () => {}
                                ,
                                deltaY: -1
                            }),
                            children: c($r, {
                                size: 15
                            })
                        }), c("button", {
                            title: "缩小",
                            className: "tool-button",
                            onClick: () => O.handleZoom({
                                preventDefault: () => {}
                                ,
                                deltaY: 1
                            }),
                            children: c(Hr, {
                                size: 15
                            })
                        }), c("button", {
                            title: "逆时针旋转",
                            className: "tool-button",
                            onClick: () => {
                                O.state.rotation -= 90,
                                O.updateTransform()
                            }
                            ,
                            children: c(wr, {
                                size: 15
                            })
                        }), c("button", {
                            title: "顺时针旋转",
                            className: "tool-button",
                            onClick: () => {
                                O.state.rotation += 90,
                                O.updateTransform()
                            }
                            ,
                            children: c(kr, {
                                size: 15
                            })
                        }), c("button", {
                            title: "左移",
                            className: "tool-button",
                            onClick: () => {
                                O.state.panX -= 10,
                                O.updateTransform()
                            }
                            ,
                            children: c(Va, {
                                size: 15
                            })
                        }), c("button", {
                            title: "上移",
                            className: "tool-button",
                            onClick: () => {
                                O.state.panY -= 10,
                                O.updateTransform()
                            }
                            ,
                            children: c(Ja, {
                                size: 15
                            })
                        }), c("button", {
                            title: "下移",
                            className: "tool-button",
                            onClick: () => {
                                O.state.panY += 10,
                                O.updateTransform()
                            }
                            ,
                            children: c(Ha, {
                                size: 15
                            })
                        }), c("button", {
                            title: "右移",
                            className: "tool-button",
                            onClick: () => {
                                O.state.panX += 10,
                                O.updateTransform()
                            }
                            ,
                            children: c(Xa, {
                                size: 15
                            })
                        })]
                    }), c("div", {
                        className: "flex-group",
                        children: [c("button", {
                            onClick: () => t("鼠标：左键拖动平移，滚轮缩放，右键或Alt+左键拖动旋转。触摸：单指拖动平移，双指捏合缩放。除此之外，还可以使用下面按钮执行上述操作。", "裁剪模式帮助"),
                            children: "帮助"
                        }), c("button", {
                            onClick: () => {
                                O.resetStates(!0),
                                O.updateTransform()
                            }
                            ,
                            children: "重置"
                        }), c("button", {
                            className: "primary",
                            onClick: () => Gn(),
                            children: "完成"
                        })]
                    })]
                }), c("div", {
                    className: "flex-container",
                    children: c("div", {
                        className: "flex-group",
                        children: [c("button", {
                            title: "画笔",
                            className: `tool-button ${B === "brush" ? "active" : ""}`,
                            disabled: oe,
                            onClick: () => it("brush"),
                            children: c(br, {
                                size: 15
                            })
                        }), c("button", {
                            title: "橡皮擦",
                            className: `tool-button ${B === "eraser" ? "active" : ""}`,
                            disabled: oe,
                            onClick: () => it("eraser"),
                            children: c(rr, {
                                size: 15
                            })
                        }), c("button", {
                            title: "添加文字",
                            className: `tool-button ${B === "text" ? "active" : ""}`,
                            disabled: oe,
                            onClick: () => it("text"),
                            children: c(Pr, {
                                size: 15
                            })
                        }), c("button", {
                            title: "加载模板",
                            className: `tool-button ${B === "tmpl" ? "active" : ""}`,
                            disabled: oe,
                            onClick: () => it("tmpl"),
                            children: c(pr, {
                                size: 15
                            })
                        }), B && c(Ne, {
                            children: [c("button", {
                                title: "撤销 (Ctrl+Z)",
                                className: "tool-button",
                                disabled: oe || K,
                                onClick: () => P.undo(),
                                children: c(Ur, {
                                    size: 15
                                })
                            }), c("button", {
                                title: "重做 (Ctrl+Y)",
                                className: "tool-button",
                                disabled: oe || V,
                                onClick: () => P.redo(),
                                children: c(vr, {
                                    size: 15
                                })
                            })]
                        })]
                    })
                }), (B === "brush" || B === "eraser" || B === "text") && c("div", {
                    className: "flex-container",
                    children: c("div", {
                        className: "flex-group",
                        children: [c("label", {
                            children: "颜色:"
                        }), c("select", {
                            value: ve,
                            disabled: B === "eraser",
                            onChange: g => {
                                d(g.target.value),
                                P.setBrushColor(g.target.value)
                            }
                            ,
                            children: [c("option", {
                                value: "#000000",
                                children: "黑色"
                            }), c("option", {
                                value: "#FF0000",
                                children: "红色"
                            }), c("option", {
                                value: "#FFFF00",
                                children: "黄色"
                            }), c("option", {
                                value: "#00FF00",
                                children: "绿色"
                            }), c("option", {
                                value: "#0000FF",
                                children: "蓝色"
                            }), c("option", {
                                value: "#FFFFFF",
                                children: "白色"
                            })]
                        }), c("label", {
                            children: "粗细:"
                        }), c("input", {
                            type: "number",
                            value: u,
                            min: "1",
                            max: "100",
                            disabled: B === "text",
                            onChange: g => {
                                const R = parseInt(g.target.value);
                                C(R),
                                P.setBrushSize(R)
                            }
                        })]
                    })
                }), B === "text" && c("div", {
                    className: "flex-container",
                    children: [c("div", {
                        className: "flex-group",
                        children: [c("label", {
                            children: "字体:"
                        }), c("select", {
                            value: z,
                            onChange: g => j(g.target.value),
                            children: mo.map(g => c("option", {
                                value: g.value,
                                style: {
                                    fontFamily: g.value
                                },
                                children: g.label
                            }, g.value))
                        }), c("label", {
                            children: "大小:"
                        }), c("input", {
                            type: "number",
                            value: ae,
                            min: "1",
                            max: "100",
                            onChange: g => se(parseInt(g.target.value))
                        })]
                    }), c("div", {
                        className: "flex-group",
                        children: [c("input", {
                            type: "text",
                            value: X,
                            placeholder: "输入文字",
                            style: {
                                width: "150px"
                            },
                            onChange: g => ce(g.target.value)
                        }), c("button", {
                            title: "粗体",
                            className: `tool-button ${Z ? "primary" : ""}`,
                            onClick: () => {
                                ye(!Z),
                                P.setTextBold(!Z)
                            }
                            ,
                            children: c(Za, {
                                size: 15
                            })
                        }), c("button", {
                            title: "斜体",
                            className: `tool-button ${Ce ? "primary" : ""}`,
                            onClick: () => {
                                xe(!Ce),
                                P.setTextItalic(!Ce)
                            }
                            ,
                            children: c(xr, {
                                size: 15
                            })
                        }), c("button", {
                            className: "primary",
                            onClick: () => {
                                P.startTextPlacement(X, z, ae)
                            }
                            ,
                            children: "添加文字"
                        })]
                    })]
                }), B === "tmpl" && c(Ne, {
                    children: [c("div", {
                        className: "flex-container",
                        children: c("div", {
                            className: "flex-group",
                            children: [c("label", {
                                children: "选择模板:"
                            }), c("select", {
                                value: Se,
                                onChange: g => Bt(g.target.value),
                                children: [c("option", {
                                    value: "",
                                    children: "-- 选择模板 --"
                                }), Ie.filter(g => !g.hidden || de === g.name).map(g => c("option", {
                                    value: g.name,
                                    children: g.display || g.name
                                }, g.name))]
                            }), c("button", {
                                className: "primary",
                                onClick: Qn,
                                children: "重新渲染"
                            })]
                        })
                    }), ot.length > 0 && c("div", {
                        className: "flex-container tmpl-vars",
                        children: ot.map(g => c("div", {
                            className: "flex-group",
                            children: [c("label", {
                                children: [g.name, g.type === "image" ? c(nr, {
                                    size: 12,
                                    style: {
                                        display: "inline",
                                        marginLeft: "4px",
                                        verticalAlign: "middle"
                                    }
                                }) : ""]
                            }), g.type === "image" ? c("input", {
                                type: "file",
                                accept: "image/*",
                                style: {
                                    fontSize: "12px"
                                },
                                onChange: R => {
                                    const L = R.target.files;
                                    if (!L || L.length === 0)
                                        return;
                                    const H = new FileReader;
                                    H.onload = ne => {
                                        if (ne.target.result.length > 300 * 1024) {
                                            R.target.value = "",
                                            t("图片大小不能超过 200KB");
                                            return
                                        }
                                        ke(G => ({
                                            ...G,
                                            [g.name]: ne.target.result
                                        }))
                                    }
                                    ,
                                    H.readAsDataURL(L[0])
                                }
                            }) : c("input", {
                                type: "text",
                                value: we[g.name] || "",
                                placeholder: g.value || "",
                                onChange: R => ke(L => ({
                                    ...L,
                                    [g.name]: R.target.value
                                }))
                            })]
                        }, g.name))
                    })]
                })]
            })]
        })]
    })
}
function vo() {
    const {dfu: e} = Le()
      , {showAlert: t, showConfirm: n} = Be()
      , {dfuStatus: a, dfuProgress: i, dfuInfo: r, dfuFileRef: o} = e
      , x = T(async () => {
        e.isAvailable() ? await e.start() : await n("即将重启进入 DFU 模式，是否继续？", "确认") && await t("已发送进入 DFU 模式指令，请连接到名为 NRF-DFU 的蓝牙继续固件升级。(注意：部分系统可能有蓝牙缓存，导致搜到的还是原来的蓝牙名，请彻底退出打开上位机的浏览器后，到系统设置开关一次蓝牙，再重新连接）", "提示")
    }
    , [e])
      , p = T(async () => {
        e.isAvailable() && await n("即将重启设备并退出 DFU 模式，是否继续？", "确认") && e.resetChip()
    }
    , [e]);
    return c("div", {
        className: "card",
        children: [c("div", {
            className: "card-header",
            children: "固件升级"
        }), c("div", {
            className: "card-body",
            children: [c("div", {
                className: "flex-container",
                children: c("div", {
                    className: "flex-group",
                    children: [c("label", {
                        children: "固件文件:"
                    }), c("input", {
                        type: "file",
                        ref: o,
                        accept: ".bin",
                        id: "dfu-file"
                    }), c("button", {
                        type: "button",
                        className: "danger",
                        onClick: x,
                        children: "开始升级"
                    }), c("button", {
                        type: "button",
                        onClick: p,
                        children: "退出 DFU"
                    })]
                })
            }), c("div", {
                className: "flex-container",
                children: c("div", {
                    className: "flex-group",
                    children: [c("label", {
                        children: "状态:"
                    }), c("span", {
                        style: {
                            color: "var(--text-muted)"
                        },
                        children: a
                    })]
                })
            }), c("div", {
                className: "flex-container",
                children: c("progress", {
                    value: i,
                    max: "100"
                })
            }), c("div", {
                className: "flex-container",
                children: c("div", {
                    className: "flex-group",
                    children: c("span", {
                        style: {
                            color: "var(--text-subtle)",
                            fontSize: "0.82rem"
                        },
                        children: r
                    })
                })
            })]
        })]
    })
}
function yo() {
    const {debugMode: e} = Le();
    return c("div", {
        className: "footer",
        children: [c("span", {
            className: "links",
            children: [c("span", {
                className: "copy",
                children: "© 2026 tsl0922."
            }), c("a", {
                href: e ? window.location.pathname : "?debug=true",
                children: e ? "正常模式" : "开发模式"
            })]
        }), c("span", {
            className: "icp",
            children: [c("span", {
                className: "icp-item",
                children: [c("img", {
                    src: "beian.png",
                    alt: ""
                }), c("a", {
                    href: "https://beian.mps.gov.cn/#/query/webSearch?code=44030002010679",
                    rel: "noreferrer",
                    target: "_blank",
                    children: "粤公网安备44030002010679号"
                })]
            }), c("span", {
                className: "icp-item",
                children: c("a", {
                    href: "https://beian.miit.gov.cn/",
                    target: "_blank",
                    rel: "noreferrer",
                    children: "粤ICP备2026015148号-1"
                })
            })]
        })]
    })
}
const bn = {
    year: 2026,
    entries: [257, 258, 259, 4356, 4622, 527, 528, 529, 530, 531, 532, 533, 534, 535, 4636, 1028, 1029, 1030, 1281, 1282, 1283, 1284, 1285, 5385, 1555, 1556, 1557, 2329, 2330, 2331, 6420, 2561, 2562, 2563, 2564, 2565, 2566, 2567, 6666]
};
function wo({open: e, onClose: t, darkMode: n, onToggleDark: a}) {
    const {mtuSize: i, setMtuSize: r, interleavedCount: o, setInterleavedCount: x, connected: p, write: h, bleNamePrefix: m, setBleNamePrefix: l} = Le()
      , {showAlert: s} = Be()
      , w = te(null);
    Ue( () => {
        if (!e)
            return;
        const b = v => {
            v.key === "Escape" && t()
        }
        ;
        return document.addEventListener("keydown", b),
        () => document.removeEventListener("keydown", b)
    }
    , [e, t]);
    const S = T(async b => {
        await h(33, [b]),
        await s("设置指令已发送！点击“日历模式”按钮刷新日历查看效果。", "提示")
    }
    , [h, s])
      , I = T(async () => {
        const {year: b, entries: v} = bn
          , E = [];
        for (const W of v)
            E.push(W >> 8 & 255, W & 255);
        const f = i - 2
          , _ = [0, b >> 8 & 255, b & 255, v.length & 255]
          , y = Math.min(E.length, f - _.length);
        await h(be.SET_HOLIDAYS, [..._, ...E.slice(0, y)]);
        let F = y;
        for (; F < E.length; ) {
            const W = Math.min(E.length - F, f - 1);
            await h(be.SET_HOLIDAYS, [1, ...E.slice(F, F + W)]),
            F += W
        }
        await s("节假日数据已同步！稍后屏幕将自动刷新。", "提示")
    }
    , [i, h, s])
      , M = T(async () => {
        await h(be.SET_HOLIDAYS, [255]),
        await s("节假日数据已清除！稍后屏幕将自动刷新。", "提示")
    }
    , [h, s]);
    return c(Ne, {
        children: [e && c("div", {
            className: "settings-backdrop",
            onClick: t
        }), c("div", {
            className: `settings-panel ${e ? "open" : ""}`,
            ref: w,
            children: [c("div", {
                className: "settings-header",
                children: [c("span", {
                    children: "设置"
                }), c("button", {
                    className: "settings-close",
                    onClick: t,
                    title: "关闭",
                    children: c(Fr, {
                        size: 16
                    })
                })]
            }), c("div", {
                className: "settings-body",
                children: [c("div", {
                    className: "settings-section",
                    children: [c("div", {
                        className: "settings-section-title",
                        children: "外观"
                    }), c("label", {
                        className: "settings-row",
                        children: [c("span", {
                            className: "settings-label",
                            children: [n ? c(fr, {
                                size: 14
                            }) : c(Er, {
                                size: 14
                            }), "深色模式"]
                        }), c("button", {
                            className: `settings-toggle ${n ? "on" : ""}`,
                            onClick: a,
                            children: c("span", {
                                className: "settings-toggle-thumb"
                            })
                        })]
                    })]
                }), c("div", {
                    className: "settings-section",
                    children: [c("div", {
                        className: "settings-section-title",
                        children: "日历设置"
                    }), c("label", {
                        className: "settings-row",
                        children: [c("span", {
                            className: "settings-label",
                            children: "星期开始"
                        }), c("button", {
                            disabled: !p,
                            onClick: () => S(0),
                            children: "星期日"
                        }), c("button", {
                            disabled: !p,
                            onClick: () => S(1),
                            children: "星期一"
                        })]
                    })]
                }), c("div", {
                    className: "settings-section",
                    children: [c("div", {
                        className: "settings-section-title",
                        children: "节假日数据"
                    }), c("label", {
                        className: "settings-row",
                        children: [c("span", {
                            className: "settings-label",
                            children: [bn.year, " 年"]
                        }), c("button", {
                            disabled: !p,
                            onClick: I,
                            children: "同步"
                        }), c("button", {
                            disabled: !p,
                            onClick: M,
                            children: "清除"
                        })]
                    })]
                }), c("div", {
                    className: "settings-section",
                    children: [c("div", {
                        className: "settings-section-title",
                        children: "蓝牙连接"
                    }), c("div", {
                        className: "settings-row",
                        children: [c("span", {
                            className: "settings-label",
                            title: "扫描时过滤蓝牙设备名称",
                            children: "扫描过滤"
                        }), c("button", {
                            className: `settings-toggle ${m ? "on" : ""}`,
                            onClick: () => l(m ? "" : "NRF_EPD_"),
                            children: c("span", {
                                className: "settings-toggle-thumb"
                            })
                        })]
                    }), c("div", {
                        className: "settings-row",
                        children: [c("span", {
                            className: "settings-label",
                            children: "确认间隔"
                        }), c("input", {
                            className: "settings-input",
                            type: "number",
                            value: o,
                            placeholder: "10",
                            min: "0",
                            max: "50",
                            onChange: b => x(parseInt(b.target.value))
                        })]
                    }), c("div", {
                        className: "settings-row",
                        children: [c("span", {
                            className: "settings-label",
                            children: "MTU"
                        }), c("input", {
                            className: "settings-input",
                            type: "number",
                            value: i,
                            min: "0",
                            max: "512",
                            onChange: b => r(parseInt(b.target.value))
                        })]
                    })]
                })]
            })]
        })]
    })
}
function Co() {
    const {dfuMode: e, dfuAvailable: t, debugMode: n, addLog: a} = Le()
      , {showAlert: i} = Be()
      , [r,o] = $( () => {
        const m = localStorage.getItem("darkMode");
        return m !== null ? m === "true" : !1
    }
    )
      , [x,p] = $(!1);
    return Ue( () => {
        r ? document.body.classList.add("dark-mode") : document.body.classList.remove("dark-mode"),
        localStorage.setItem("darkMode", r)
    }
    , [r]),
    Ue( () => {
        if (n) {
            const m = "开发模式功能已开启！不懂请不要随意修改，否则后果自负！";
            a(`警告：${m}`, "⚠️"),
            i(m, "警告")
        }
    }
    , [n]),
    c(Ne, {
        children: [c(Br, {
            onSettingsClick: () => p(m => !m)
        }), c("div", {
            className: "main",
            children: [c(jr, {}), !e && c(Xr, {}), !e && c(go, {}), n && t && c(vo, {})]
        }), c(yo, {}), c(wo, {
            open: x,
            onClose: () => p(!1),
            darkMode: r,
            onToggleDark: () => o(m => !m)
        })]
    })
}
function ko() {
    return c(Ea, {
        children: c(za, {
            children: c(Co, {})
        })
    })
}
Da.createRoot(document.getElementById("root")).render(c(Ma.StrictMode, {
    children: c(ko, {})
}));
