var __defProp = Object.defineProperty;
var __getOwnPropSymbols = Object.getOwnPropertySymbols;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __propIsEnum = Object.prototype.propertyIsEnumerable;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __spreadValues = (a, b) => {
  for (var prop in b || (b = {}))
    if (__hasOwnProp.call(b, prop))
      __defNormalProp(a, prop, b[prop]);
  if (__getOwnPropSymbols)
    for (var prop of __getOwnPropSymbols(b)) {
      if (__propIsEnum.call(b, prop))
        __defNormalProp(a, prop, b[prop]);
    }
  return a;
};
import { l as listen, i as bubble, p as prevent_default, j as stop_propagation, c as create_ssr_component, a as compute_rest_props, g as get_current_component, b as spread, d as escape_attribute_value, f as escape_object, h as add_attribute, s as setContext, v as validate_component, k as each, n as globals, o as getContext, m as missing_component, e as escape, q as onDestroy } from "./index-3c4e05aa.js";
import "@material/tab-bar";
import "@material/tab-scroller";
import { events, ponyfill } from "@material/dom";
import "@material/tab";
import { MDCRippleFoundation, util } from "@material/ripple";
import { MDCFadingTabIndicatorFoundation, MDCSlidingTabIndicatorFoundation } from "@material/tab-indicator";
function classMap(classObj) {
  return Object.entries(classObj).filter(([name, value]) => name !== "" && value).map(([name]) => name).join(" ");
}
function exclude(obj, keys) {
  let names = Object.getOwnPropertyNames(obj);
  const newObj = {};
  for (let i = 0; i < names.length; i++) {
    const name = names[i];
    const cashIndex = name.indexOf("$");
    if (cashIndex !== -1 && keys.indexOf(name.substring(0, cashIndex + 1)) !== -1) {
      continue;
    }
    if (keys.indexOf(name) !== -1) {
      continue;
    }
    newObj[name] = obj[name];
  }
  return newObj;
}
const oldModifierRegex = /^[a-z]+(?::(?:preventDefault|stopPropagation|passive|nonpassive|capture|once|self))+$/;
const newModifierRegex = /^[^$]+(?:\$(?:preventDefault|stopPropagation|passive|nonpassive|capture|once|self))+$/;
function forwardEventsBuilder(component) {
  let $on;
  let events2 = [];
  component.$on = (fullEventType, callback) => {
    let eventType = fullEventType;
    let destructor = () => {
    };
    if ($on) {
      destructor = $on(eventType, callback);
    } else {
      events2.push([eventType, callback]);
    }
    const oldModifierMatch = eventType.match(oldModifierRegex);
    if (oldModifierMatch && console) {
      console.warn('Event modifiers in SMUI now use "$" instead of ":", so that all events can be bound with modifiers. Please update your event binding: ', eventType);
    }
    return () => {
      destructor();
    };
  };
  function forward(e) {
    bubble(component, e);
  }
  return (node) => {
    const destructors = [];
    const forwardDestructors = {};
    $on = (fullEventType, callback) => {
      let eventType = fullEventType;
      let handler = callback;
      let options = false;
      const oldModifierMatch = eventType.match(oldModifierRegex);
      const newModifierMatch = eventType.match(newModifierRegex);
      const modifierMatch = oldModifierMatch || newModifierMatch;
      if (eventType.match(/^SMUI:\w+:/)) {
        const newEventTypeParts = eventType.split(":");
        let newEventType = "";
        for (let i = 0; i < newEventTypeParts.length; i++) {
          newEventType += i === newEventTypeParts.length - 1 ? ":" + newEventTypeParts[i] : newEventTypeParts[i].split("-").map((value) => value.slice(0, 1).toUpperCase() + value.slice(1)).join("");
        }
        console.warn(`The event ${eventType.split("$")[0]} has been renamed to ${newEventType.split("$")[0]}.`);
        eventType = newEventType;
      }
      if (modifierMatch) {
        const parts = eventType.split(oldModifierMatch ? ":" : "$");
        eventType = parts[0];
        const eventOptions = Object.fromEntries(parts.slice(1).map((mod) => [mod, true]));
        if (eventOptions.passive) {
          options = options || {};
          options.passive = true;
        }
        if (eventOptions.nonpassive) {
          options = options || {};
          options.passive = false;
        }
        if (eventOptions.capture) {
          options = options || {};
          options.capture = true;
        }
        if (eventOptions.once) {
          options = options || {};
          options.once = true;
        }
        if (eventOptions.preventDefault) {
          handler = prevent_default(handler);
        }
        if (eventOptions.stopPropagation) {
          handler = stop_propagation(handler);
        }
      }
      const off = listen(node, eventType, handler, options);
      const destructor = () => {
        off();
        const idx = destructors.indexOf(destructor);
        if (idx > -1) {
          destructors.splice(idx, 1);
        }
      };
      destructors.push(destructor);
      if (!(eventType in forwardDestructors)) {
        forwardDestructors[eventType] = listen(node, eventType, forward);
      }
      return destructor;
    };
    for (let i = 0; i < events2.length; i++) {
      $on(events2[i][0], events2[i][1]);
    }
    return {
      destroy: () => {
        for (let i = 0; i < destructors.length; i++) {
          destructors[i]();
        }
        for (let entry of Object.entries(forwardDestructors)) {
          entry[1]();
        }
      }
    };
  };
}
function prefixFilter(obj, prefix) {
  let names = Object.getOwnPropertyNames(obj);
  const newObj = {};
  for (let i = 0; i < names.length; i++) {
    const name = names[i];
    if (name.substring(0, prefix.length) === prefix) {
      newObj[name.substring(prefix.length)] = obj[name];
    }
  }
  return newObj;
}
const TabScroller = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, [
    "use",
    "class",
    "align",
    "scrollArea$use",
    "scrollArea$class",
    "scrollContent$use",
    "scrollContent$class",
    "getScrollPosition",
    "getScrollContentWidth",
    "incrementScroll",
    "scrollTo",
    "getElement"
  ]);
  forwardEventsBuilder(get_current_component());
  let { use = [] } = $$props;
  let { class: className = "" } = $$props;
  let { align = void 0 } = $$props;
  let { scrollArea$use = [] } = $$props;
  let { scrollArea$class = "" } = $$props;
  let { scrollContent$use = [] } = $$props;
  let { scrollContent$class = "" } = $$props;
  let element;
  let instance;
  let scrollArea;
  let scrollContent;
  let internalClasses = {};
  let scrollAreaClasses = {};
  let scrollAreaStyles = {};
  let scrollContentStyles = {};
  function getScrollPosition() {
    return instance.getScrollPosition();
  }
  function getScrollContentWidth() {
    return scrollContent.offsetWidth;
  }
  function incrementScroll(scrollXIncrement) {
    instance.incrementScroll(scrollXIncrement);
  }
  function scrollTo(scrollX) {
    instance.scrollTo(scrollX);
  }
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.class === void 0 && $$bindings.class && className !== void 0)
    $$bindings.class(className);
  if ($$props.align === void 0 && $$bindings.align && align !== void 0)
    $$bindings.align(align);
  if ($$props.scrollArea$use === void 0 && $$bindings.scrollArea$use && scrollArea$use !== void 0)
    $$bindings.scrollArea$use(scrollArea$use);
  if ($$props.scrollArea$class === void 0 && $$bindings.scrollArea$class && scrollArea$class !== void 0)
    $$bindings.scrollArea$class(scrollArea$class);
  if ($$props.scrollContent$use === void 0 && $$bindings.scrollContent$use && scrollContent$use !== void 0)
    $$bindings.scrollContent$use(scrollContent$use);
  if ($$props.scrollContent$class === void 0 && $$bindings.scrollContent$class && scrollContent$class !== void 0)
    $$bindings.scrollContent$class(scrollContent$class);
  if ($$props.getScrollPosition === void 0 && $$bindings.getScrollPosition && getScrollPosition !== void 0)
    $$bindings.getScrollPosition(getScrollPosition);
  if ($$props.getScrollContentWidth === void 0 && $$bindings.getScrollContentWidth && getScrollContentWidth !== void 0)
    $$bindings.getScrollContentWidth(getScrollContentWidth);
  if ($$props.incrementScroll === void 0 && $$bindings.incrementScroll && incrementScroll !== void 0)
    $$bindings.incrementScroll(incrementScroll);
  if ($$props.scrollTo === void 0 && $$bindings.scrollTo && scrollTo !== void 0)
    $$bindings.scrollTo(scrollTo);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<div${spread([
    {
      class: escape_attribute_value(classMap(__spreadValues({
        [className]: true,
        "mdc-tab-scroller": true,
        "mdc-tab-scroller--align-start": align === "start",
        "mdc-tab-scroller--align-end": align === "end",
        "mdc-tab-scroller--align-center": align === "center"
      }, internalClasses)))
    },
    escape_object(exclude($$restProps, ["scrollArea$", "scrollContent$"]))
  ], {})}${add_attribute("this", element, 0)}><div${spread([
    {
      class: escape_attribute_value(classMap(__spreadValues({
        [scrollArea$class]: true,
        "mdc-tab-scroller__scroll-area": true
      }, scrollAreaClasses)))
    },
    {
      style: escape_attribute_value(Object.entries(scrollAreaStyles).map(([name, value]) => `${name}: ${value};`).join(" "))
    },
    escape_object(prefixFilter($$restProps, "scrollArea$"))
  ], {})}${add_attribute("this", scrollArea, 0)}><div${spread([
    {
      class: escape_attribute_value(classMap({
        [scrollContent$class]: true,
        "mdc-tab-scroller__scroll-content": true
      }))
    },
    {
      style: escape_attribute_value(Object.entries(scrollContentStyles).map(([name, value]) => `${name}: ${value};`).join(" "))
    },
    escape_object(prefixFilter($$restProps, "scrollContent$"))
  ], {})}${add_attribute("this", scrollContent, 0)}>${slots.default ? slots.default({}) : ``}</div></div>
</div>`;
});
const { Object: Object_1$2 } = globals;
const TabBar = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, [
    "use",
    "class",
    "tabs",
    "key",
    "focusOnActivate",
    "focusOnProgrammatic",
    "useAutomaticActivation",
    "active",
    "scrollIntoView",
    "getElement"
  ]);
  forwardEventsBuilder(get_current_component());
  let { use = [] } = $$props;
  let { class: className = "" } = $$props;
  let { tabs = [] } = $$props;
  let { key = (tab) => tab } = $$props;
  let { focusOnActivate = true } = $$props;
  let { focusOnProgrammatic = false } = $$props;
  let { useAutomaticActivation = true } = $$props;
  let { active = void 0 } = $$props;
  let element;
  let instance;
  let tabScroller;
  let activeIndex = tabs.indexOf(active);
  let tabAccessorMap = {};
  let tabAccessorWeakMap = /* @__PURE__ */ new WeakMap();
  setContext("SMUI:tab:focusOnActivate", focusOnActivate);
  setContext("SMUI:tab:initialActive", active);
  function scrollIntoView(index) {
    instance.scrollIntoView(index);
  }
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.class === void 0 && $$bindings.class && className !== void 0)
    $$bindings.class(className);
  if ($$props.tabs === void 0 && $$bindings.tabs && tabs !== void 0)
    $$bindings.tabs(tabs);
  if ($$props.key === void 0 && $$bindings.key && key !== void 0)
    $$bindings.key(key);
  if ($$props.focusOnActivate === void 0 && $$bindings.focusOnActivate && focusOnActivate !== void 0)
    $$bindings.focusOnActivate(focusOnActivate);
  if ($$props.focusOnProgrammatic === void 0 && $$bindings.focusOnProgrammatic && focusOnProgrammatic !== void 0)
    $$bindings.focusOnProgrammatic(focusOnProgrammatic);
  if ($$props.useAutomaticActivation === void 0 && $$bindings.useAutomaticActivation && useAutomaticActivation !== void 0)
    $$bindings.useAutomaticActivation(useAutomaticActivation);
  if ($$props.active === void 0 && $$bindings.active && active !== void 0)
    $$bindings.active(active);
  if ($$props.scrollIntoView === void 0 && $$bindings.scrollIntoView && scrollIntoView !== void 0)
    $$bindings.scrollIntoView(scrollIntoView);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  let $$settled;
  let $$rendered;
  do {
    $$settled = true;
    {
      if (active !== tabs[activeIndex]) {
        activeIndex = tabs.indexOf(active);
      }
    }
    {
      if (tabs.length) {
        const accessor = tabs[0] instanceof Object ? tabAccessorWeakMap.get(tabs[0]) : tabAccessorMap[tabs[0]];
        if (accessor) {
          accessor.forceAccessible(activeIndex === -1);
        }
      }
    }
    $$rendered = `<div${spread([
      {
        class: escape_attribute_value(classMap({ [className]: true, "mdc-tab-bar": true }))
      },
      { role: "tablist" },
      escape_object(exclude($$restProps, ["tabScroller$"]))
    ], {})}${add_attribute("this", element, 0)}>${validate_component(TabScroller, "TabScroller").$$render($$result, Object_1$2.assign(prefixFilter($$restProps, "tabScroller$"), { this: tabScroller }), {
      this: ($$value) => {
        tabScroller = $$value;
        $$settled = false;
      }
    }, {
      default: () => {
        return `${each(tabs, (tab) => {
          return `${slots.default ? slots.default({ tab }) : ``}`;
        })}`;
      }
    })}
</div>`;
  } while (!$$settled);
  return $$rendered;
});
const { applyPassive } = events;
const { matches } = ponyfill;
function Ripple(node, { ripple = true, surface = false, unbounded = false, disabled = false, color, active, rippleElement, eventTarget, activeTarget, addClass = (className) => node.classList.add(className), removeClass = (className) => node.classList.remove(className), addStyle = (name, value) => node.style.setProperty(name, value), initPromise = Promise.resolve() } = {}) {
  let instance;
  let addLayoutListener = getContext("SMUI:addLayoutListener");
  let removeLayoutListener;
  let oldActive = active;
  let oldEventTarget = eventTarget;
  let oldActiveTarget = activeTarget;
  function handleProps() {
    if (surface) {
      addClass("mdc-ripple-surface");
      if (color === "primary") {
        addClass("smui-ripple-surface--primary");
        removeClass("smui-ripple-surface--secondary");
      } else if (color === "secondary") {
        removeClass("smui-ripple-surface--primary");
        addClass("smui-ripple-surface--secondary");
      } else {
        removeClass("smui-ripple-surface--primary");
        removeClass("smui-ripple-surface--secondary");
      }
    } else {
      removeClass("mdc-ripple-surface");
      removeClass("smui-ripple-surface--primary");
      removeClass("smui-ripple-surface--secondary");
    }
    if (instance && oldActive !== active) {
      oldActive = active;
      if (active) {
        instance.activate();
      } else if (active === false) {
        instance.deactivate();
      }
    }
    if (ripple && !instance) {
      instance = new MDCRippleFoundation({
        addClass,
        browserSupportsCssVars: () => util.supportsCssVariables(window),
        computeBoundingRect: () => (rippleElement || node).getBoundingClientRect(),
        containsEventTarget: (target) => node.contains(target),
        deregisterDocumentInteractionHandler: (evtType, handler) => document.documentElement.removeEventListener(evtType, handler, applyPassive()),
        deregisterInteractionHandler: (evtType, handler) => (eventTarget || node).removeEventListener(evtType, handler, applyPassive()),
        deregisterResizeHandler: (handler) => window.removeEventListener("resize", handler),
        getWindowPageOffset: () => ({
          x: window.pageXOffset,
          y: window.pageYOffset
        }),
        isSurfaceActive: () => active == null ? matches(activeTarget || node, ":active") : active,
        isSurfaceDisabled: () => !!disabled,
        isUnbounded: () => !!unbounded,
        registerDocumentInteractionHandler: (evtType, handler) => document.documentElement.addEventListener(evtType, handler, applyPassive()),
        registerInteractionHandler: (evtType, handler) => (eventTarget || node).addEventListener(evtType, handler, applyPassive()),
        registerResizeHandler: (handler) => window.addEventListener("resize", handler),
        removeClass,
        updateCssVariable: addStyle
      });
      initPromise.then(() => {
        if (instance) {
          instance.init();
          instance.setUnbounded(unbounded);
        }
      });
    } else if (instance && !ripple) {
      initPromise.then(() => {
        if (instance) {
          instance.destroy();
          instance = void 0;
        }
      });
    }
    if (instance && (oldEventTarget !== eventTarget || oldActiveTarget !== activeTarget)) {
      oldEventTarget = eventTarget;
      oldActiveTarget = activeTarget;
      instance.destroy();
      requestAnimationFrame(() => {
        if (instance) {
          instance.init();
          instance.setUnbounded(unbounded);
        }
      });
    }
    if (!ripple && unbounded) {
      addClass("mdc-ripple-upgraded--unbounded");
    }
  }
  handleProps();
  if (addLayoutListener) {
    removeLayoutListener = addLayoutListener(layout);
  }
  function layout() {
    if (instance) {
      instance.layout();
    }
  }
  return {
    update(props) {
      ({
        ripple,
        surface,
        unbounded,
        disabled,
        color,
        active,
        rippleElement,
        eventTarget,
        activeTarget,
        addClass,
        removeClass,
        addStyle,
        initPromise
      } = Object.assign({ ripple: true, surface: false, unbounded: false, disabled: false, color: void 0, active: void 0, rippleElement: void 0, eventTarget: void 0, activeTarget: void 0, addClass: (className) => node.classList.add(className), removeClass: (className) => node.classList.remove(className), addStyle: (name, value) => node.style.setProperty(name, value), initPromise: Promise.resolve() }, props));
      handleProps();
    },
    destroy() {
      if (instance) {
        instance.destroy();
        instance = void 0;
        removeClass("mdc-ripple-surface");
        removeClass("smui-ripple-surface--primary");
        removeClass("smui-ripple-surface--secondary");
      }
      if (removeLayoutListener) {
        removeLayoutListener();
      }
    }
  };
}
const A$1 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "href", "getElement"]);
  let { use = [] } = $$props;
  let { href = "javascript:void(0);" } = $$props;
  forwardEventsBuilder(get_current_component());
  let element;
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.href === void 0 && $$bindings.href && href !== void 0)
    $$bindings.href(href);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<a${spread([{ href: escape_attribute_value(href) }, escape_object($$restProps)], {})}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}</a>`;
});
const Button$1 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "getElement"]);
  let { use = [] } = $$props;
  forwardEventsBuilder(get_current_component());
  let element;
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<button${spread([escape_object($$restProps)], {})}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}</button>`;
});
const Div$1 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "getElement"]);
  let { use = [] } = $$props;
  forwardEventsBuilder(get_current_component());
  let element;
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<div${spread([escape_object($$restProps)], {})}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}
</div>`;
});
const H1$1 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "getElement"]);
  let { use = [] } = $$props;
  forwardEventsBuilder(get_current_component());
  let element;
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<h1${spread([escape_object($$restProps)], {})}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}
</h1>`;
});
const H2$1 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "getElement"]);
  let { use = [] } = $$props;
  forwardEventsBuilder(get_current_component());
  let element;
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<h2${spread([escape_object($$restProps)], {})}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}
</h2>`;
});
const H3$1 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "getElement"]);
  let { use = [] } = $$props;
  forwardEventsBuilder(get_current_component());
  let element;
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<h3${spread([escape_object($$restProps)], {})}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}
</h3>`;
});
const H5$1 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "getElement"]);
  let { use = [] } = $$props;
  forwardEventsBuilder(get_current_component());
  let element;
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<h5${spread([escape_object($$restProps)], {})}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}
</h5>`;
});
const H6$1 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "getElement"]);
  let { use = [] } = $$props;
  forwardEventsBuilder(get_current_component());
  let element;
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<h6${spread([escape_object($$restProps)], {})}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}
</h6>`;
});
const Li$1 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "getElement"]);
  let { use = [] } = $$props;
  forwardEventsBuilder(get_current_component());
  let element;
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<li${spread([escape_object($$restProps)], {})}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}
</li>`;
});
const Nav$1 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "getElement"]);
  let { use = [] } = $$props;
  forwardEventsBuilder(get_current_component());
  let element;
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<nav${spread([escape_object($$restProps)], {})}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}
</nav>`;
});
const Span$1 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "getElement"]);
  let { use = [] } = $$props;
  forwardEventsBuilder(get_current_component());
  let element;
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<span${spread([escape_object($$restProps)], {})}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}</span>`;
});
const Ul$1 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "getElement"]);
  let { use = [] } = $$props;
  forwardEventsBuilder(get_current_component());
  let element;
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  return `<ul${spread([escape_object($$restProps)], {})}${add_attribute("this", element, 0)}>${slots.default ? slots.default({}) : ``}
</ul>`;
});
const A = A$1;
const Button = Button$1;
const Div = Div$1;
const H1 = H1$1;
const H2 = H2$1;
const H3 = H3$1;
const H5 = H5$1;
const H6 = H6$1;
const Li = Li$1;
const Nav = Nav$1;
const Span = Span$1;
const Ul = Ul$1;
const TabIndicator = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, [
    "use",
    "class",
    "active",
    "type",
    "transition",
    "content$use",
    "content$class",
    "activate",
    "deactivate",
    "computeContentClientRect",
    "getElement"
  ]);
  forwardEventsBuilder(get_current_component());
  let { use = [] } = $$props;
  let { class: className = "" } = $$props;
  let { active = false } = $$props;
  let { type = "underline" } = $$props;
  let { transition = "slide" } = $$props;
  let { content$use = [] } = $$props;
  let { content$class = "" } = $$props;
  let element;
  let instance;
  let content;
  let internalClasses = {};
  let contentStyles = {};
  let changeSets = [];
  let oldTransition = transition;
  function getInstance() {
    const Foundation = {
      fade: MDCFadingTabIndicatorFoundation,
      slide: MDCSlidingTabIndicatorFoundation
    }[transition] || MDCSlidingTabIndicatorFoundation;
    return new Foundation({
      addClass: (...props) => doChange(() => addClass(...props)),
      removeClass: (...props) => doChange(() => removeClass(...props)),
      computeContentClientRect,
      setContentStyleProperty: (...props) => doChange(() => addContentStyle(...props))
    });
  }
  function doChange(fn) {
    if (changeSets.length) {
      changeSets[changeSets.length - 1].push(fn);
    } else {
      fn();
    }
  }
  function addClass(className2) {
    if (!internalClasses[className2]) {
      internalClasses[className2] = true;
    }
  }
  function removeClass(className2) {
    if (!(className2 in internalClasses) || internalClasses[className2]) {
      internalClasses[className2] = false;
    }
  }
  function addContentStyle(name, value) {
    if (contentStyles[name] != value) {
      if (value === "" || value == null) {
        delete contentStyles[name];
        contentStyles = contentStyles;
      } else {
        contentStyles[name] = value;
      }
    }
  }
  function activate(previousIndicatorClientRect) {
    active = true;
    instance.activate(previousIndicatorClientRect);
  }
  function deactivate() {
    active = false;
    instance.deactivate();
  }
  function computeContentClientRect() {
    changeSets.push([]);
    changeSets = changeSets;
    return content.getBoundingClientRect();
  }
  function getElement() {
    return element;
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.class === void 0 && $$bindings.class && className !== void 0)
    $$bindings.class(className);
  if ($$props.active === void 0 && $$bindings.active && active !== void 0)
    $$bindings.active(active);
  if ($$props.type === void 0 && $$bindings.type && type !== void 0)
    $$bindings.type(type);
  if ($$props.transition === void 0 && $$bindings.transition && transition !== void 0)
    $$bindings.transition(transition);
  if ($$props.content$use === void 0 && $$bindings.content$use && content$use !== void 0)
    $$bindings.content$use(content$use);
  if ($$props.content$class === void 0 && $$bindings.content$class && content$class !== void 0)
    $$bindings.content$class(content$class);
  if ($$props.activate === void 0 && $$bindings.activate && activate !== void 0)
    $$bindings.activate(activate);
  if ($$props.deactivate === void 0 && $$bindings.deactivate && deactivate !== void 0)
    $$bindings.deactivate(deactivate);
  if ($$props.computeContentClientRect === void 0 && $$bindings.computeContentClientRect && computeContentClientRect !== void 0)
    $$bindings.computeContentClientRect(computeContentClientRect);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  {
    if (oldTransition !== transition) {
      oldTransition = transition;
      instance && instance.destroy();
      internalClasses = {};
      contentStyles = {};
      instance = getInstance();
      instance.init();
    }
  }
  {
    if (changeSets.length) {
      requestAnimationFrame(() => {
        var _a;
        const changeSet = (_a = changeSets.shift()) !== null && _a !== void 0 ? _a : [];
        changeSets = changeSets;
        for (const fn of changeSet) {
          fn();
        }
      });
    }
  }
  return `<span${spread([
    {
      class: escape_attribute_value(classMap(__spreadValues({
        [className]: true,
        "mdc-tab-indicator": true,
        "mdc-tab-indicator--active": active,
        "mdc-tab-indicator--fade": transition === "fade"
      }, internalClasses)))
    },
    escape_object(exclude($$restProps, ["content$"]))
  ], {})}${add_attribute("this", element, 0)}><span${spread([
    {
      class: escape_attribute_value(classMap({
        [content$class]: true,
        "mdc-tab-indicator__content": true,
        "mdc-tab-indicator__content--underline": type === "underline",
        "mdc-tab-indicator__content--icon": type === "icon"
      }))
    },
    {
      style: escape_attribute_value(Object.entries(contentStyles).map(([name, value]) => `${name}: ${value};`).join(" "))
    },
    {
      "aria-hidden": escape_attribute_value(type === "icon" ? "true" : void 0)
    },
    escape_object(prefixFilter($$restProps, "content$"))
  ], {})}${add_attribute("this", content, 0)}>${slots.default ? slots.default({}) : ``}</span>
</span>`;
});
const { Object: Object_1$1 } = globals;
const Tab = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, [
    "use",
    "class",
    "style",
    "tab",
    "ripple",
    "stacked",
    "minWidth",
    "indicatorSpanOnlyContent",
    "href",
    "content$use",
    "content$class",
    "component",
    "activate",
    "deactivate",
    "focus",
    "getElement"
  ]);
  const forwardEvents = forwardEventsBuilder(get_current_component());
  let { use = [] } = $$props;
  let { class: className = "" } = $$props;
  let { style = "" } = $$props;
  let { tab: tabId } = $$props;
  let { ripple = true } = $$props;
  let { stacked = false } = $$props;
  let { minWidth = false } = $$props;
  let { indicatorSpanOnlyContent = false } = $$props;
  let { href = void 0 } = $$props;
  let { content$use = [] } = $$props;
  let { content$class = "" } = $$props;
  let element;
  let instance;
  let content;
  let tabIndicator;
  let internalClasses = {};
  let internalStyles = {};
  let internalAttrs = {};
  let focusOnActivate = getContext("SMUI:tab:focusOnActivate");
  let active = tabId === getContext("SMUI:tab:initialActive");
  let forceAccessible = false;
  let { component = href == null ? Button : A } = $$props;
  setContext("SMUI:label:context", "tab");
  setContext("SMUI:icon:context", "tab");
  if (!tabId) {
    throw new Error("The tab property is required! It should be passed down from the TabBar to the Tab.");
  }
  function addClass(className2) {
    if (!internalClasses[className2]) {
      internalClasses[className2] = true;
    }
  }
  function removeClass(className2) {
    if (!(className2 in internalClasses) || internalClasses[className2]) {
      internalClasses[className2] = false;
    }
  }
  function addStyle(name, value) {
    if (internalStyles[name] != value) {
      if (value === "" || value == null) {
        delete internalStyles[name];
        internalStyles = internalStyles;
      } else {
        internalStyles[name] = value;
      }
    }
  }
  function activate(previousIndicatorClientRect, skipFocus) {
    active = true;
    if (skipFocus) {
      instance.setFocusOnActivate(false);
    }
    instance.activate(previousIndicatorClientRect);
    if (skipFocus) {
      instance.setFocusOnActivate(focusOnActivate);
    }
  }
  function deactivate() {
    active = false;
    instance.deactivate();
  }
  function focus() {
    getElement().focus();
  }
  function getElement() {
    return element.getElement();
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.class === void 0 && $$bindings.class && className !== void 0)
    $$bindings.class(className);
  if ($$props.style === void 0 && $$bindings.style && style !== void 0)
    $$bindings.style(style);
  if ($$props.tab === void 0 && $$bindings.tab && tabId !== void 0)
    $$bindings.tab(tabId);
  if ($$props.ripple === void 0 && $$bindings.ripple && ripple !== void 0)
    $$bindings.ripple(ripple);
  if ($$props.stacked === void 0 && $$bindings.stacked && stacked !== void 0)
    $$bindings.stacked(stacked);
  if ($$props.minWidth === void 0 && $$bindings.minWidth && minWidth !== void 0)
    $$bindings.minWidth(minWidth);
  if ($$props.indicatorSpanOnlyContent === void 0 && $$bindings.indicatorSpanOnlyContent && indicatorSpanOnlyContent !== void 0)
    $$bindings.indicatorSpanOnlyContent(indicatorSpanOnlyContent);
  if ($$props.href === void 0 && $$bindings.href && href !== void 0)
    $$bindings.href(href);
  if ($$props.content$use === void 0 && $$bindings.content$use && content$use !== void 0)
    $$bindings.content$use(content$use);
  if ($$props.content$class === void 0 && $$bindings.content$class && content$class !== void 0)
    $$bindings.content$class(content$class);
  if ($$props.component === void 0 && $$bindings.component && component !== void 0)
    $$bindings.component(component);
  if ($$props.activate === void 0 && $$bindings.activate && activate !== void 0)
    $$bindings.activate(activate);
  if ($$props.deactivate === void 0 && $$bindings.deactivate && deactivate !== void 0)
    $$bindings.deactivate(deactivate);
  if ($$props.focus === void 0 && $$bindings.focus && focus !== void 0)
    $$bindings.focus(focus);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  let $$settled;
  let $$rendered;
  do {
    $$settled = true;
    $$rendered = `${validate_component(component || missing_component, "svelte:component").$$render($$result, Object_1$1.assign({
      use: [
        [
          Ripple,
          {
            ripple,
            unbounded: false,
            addClass,
            removeClass,
            addStyle
          }
        ],
        forwardEvents,
        ...use
      ]
    }, {
      class: classMap(__spreadValues({
        [className]: true,
        "mdc-tab": true,
        "mdc-tab--active": active,
        "mdc-tab--stacked": stacked,
        "mdc-tab--min-width": minWidth
      }, internalClasses))
    }, {
      style: Object.entries(internalStyles).map(([name, value]) => `${name}: ${value};`).concat([style]).join(" ")
    }, { role: "tab" }, {
      "aria-selected": active ? "true" : "false"
    }, {
      tabindex: active || forceAccessible ? "0" : "-1"
    }, { href }, internalAttrs, exclude($$restProps, ["content$", "tabIndicator$"]), { this: element }), {
      this: ($$value) => {
        element = $$value;
        $$settled = false;
      }
    }, {
      default: () => {
        return `<span${spread([
          {
            class: escape_attribute_value(classMap({
              [content$class]: true,
              "mdc-tab__content": true
            }))
          },
          escape_object(prefixFilter($$restProps, "content$"))
        ], {})}${add_attribute("this", content, 0)}>${slots.default ? slots.default({}) : ``}
    ${indicatorSpanOnlyContent ? `${validate_component(TabIndicator, "TabIndicator").$$render($$result, Object_1$1.assign({ active }, prefixFilter($$restProps, "tabIndicator$"), { this: tabIndicator }), {
          this: ($$value) => {
            tabIndicator = $$value;
            $$settled = false;
          }
        }, {
          default: () => {
            return `${slots["tab-indicator"] ? slots["tab-indicator"]({}) : ``}`;
          }
        })}` : ``}</span>
  ${!indicatorSpanOnlyContent ? `${validate_component(TabIndicator, "TabIndicator").$$render($$result, Object_1$1.assign({ active }, prefixFilter($$restProps, "tabIndicator$"), { this: tabIndicator }), {
          this: ($$value) => {
            tabIndicator = $$value;
            $$settled = false;
          }
        }, {
          default: () => {
            return `${slots["tab-indicator"] ? slots["tab-indicator"]({}) : ``}`;
          }
        })}` : ``}
  <span class="${"mdc-tab__ripple"}"></span>`;
      }
    })}`;
  } while (!$$settled);
  return $$rendered;
});
const CommonLabel = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "class", "component", "getElement"]);
  const forwardEvents = forwardEventsBuilder(get_current_component());
  let { use = [] } = $$props;
  let { class: className = "" } = $$props;
  let element;
  let { component = Span$1 } = $$props;
  const context = getContext("SMUI:label:context");
  const tabindex = getContext("SMUI:label:tabindex");
  function getElement() {
    return element.getElement();
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.class === void 0 && $$bindings.class && className !== void 0)
    $$bindings.class(className);
  if ($$props.component === void 0 && $$bindings.component && component !== void 0)
    $$bindings.component(component);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  let $$settled;
  let $$rendered;
  do {
    $$settled = true;
    $$rendered = `${validate_component(component || missing_component, "svelte:component").$$render($$result, Object.assign({ use: [forwardEvents, ...use] }, {
      class: classMap({
        [className]: true,
        "mdc-button__label": context === "button",
        "mdc-fab__label": context === "fab",
        "mdc-tab__text-label": context === "tab",
        "mdc-image-list__label": context === "image-list",
        "mdc-snackbar__label": context === "snackbar",
        "mdc-banner__text": context === "banner",
        "mdc-segmented-button__label": context === "segmented-button",
        "mdc-data-table__pagination-rows-per-page-label": context === "data-table:pagination",
        "mdc-data-table__header-cell-label": context === "data-table:sortable-header-cell"
      })
    }, context === "snackbar" ? { "aria-atomic": "false" } : {}, { tabindex }, $$restProps, { this: element }), {
      this: ($$value) => {
        element = $$value;
        $$settled = false;
      }
    }, {
      default: () => {
        return `${slots.default ? slots.default({}) : ``}`;
      }
    })}`;
  } while (!$$settled);
  return $$rendered;
});
const Label = CommonLabel;
const DefaultTabbar = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { active } = $$props;
  if ($$props.active === void 0 && $$bindings.active && active !== void 0)
    $$bindings.active(active);
  let $$settled;
  let $$rendered;
  do {
    $$settled = true;
    $$rendered = `${validate_component(TabBar, "Tabbar").$$render($$result, {
      tabs: ["Controls", "Dashboard", "About Us"],
      active
    }, {
      active: ($$value) => {
        active = $$value;
        $$settled = false;
      }
    }, {
      default: ({ tab }) => {
        return `${validate_component(Tab, "Tab").$$render($$result, { tab, href: "/" + tab }, {}, {
          default: () => {
            return `${validate_component(Label, "Label").$$render($$result, {}, {}, {
              default: () => {
                return `${escape(tab)}`;
              }
            })}`;
          }
        })}`;
      }
    })}`;
  } while (!$$settled);
  return $$rendered;
});
const { Object: Object_1 } = globals;
const internals = {
  component: Div$1,
  class: "",
  classMap: {},
  contexts: {},
  props: {}
};
const ClassAdder = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$restProps = compute_rest_props($$props, ["use", "class", "component", "getElement"]);
  let { use = [] } = $$props;
  let { class: className = "" } = $$props;
  let element;
  const smuiClass = internals.class;
  const smuiClassMap = {};
  const smuiClassUnsubscribes = [];
  const contexts = internals.contexts;
  const props = internals.props;
  let { component = internals.component } = $$props;
  Object.entries(internals.classMap).forEach(([name, context]) => {
    const store = getContext(context);
    if (store && "subscribe" in store) {
      smuiClassUnsubscribes.push(store.subscribe((value) => {
        smuiClassMap[name] = value;
      }));
    }
  });
  const forwardEvents = forwardEventsBuilder(get_current_component());
  for (let context in contexts) {
    if (contexts.hasOwnProperty(context)) {
      setContext(context, contexts[context]);
    }
  }
  onDestroy(() => {
    for (const unsubscribe of smuiClassUnsubscribes) {
      unsubscribe();
    }
  });
  function getElement() {
    return element.getElement();
  }
  if ($$props.use === void 0 && $$bindings.use && use !== void 0)
    $$bindings.use(use);
  if ($$props.class === void 0 && $$bindings.class && className !== void 0)
    $$bindings.class(className);
  if ($$props.component === void 0 && $$bindings.component && component !== void 0)
    $$bindings.component(component);
  if ($$props.getElement === void 0 && $$bindings.getElement && getElement !== void 0)
    $$bindings.getElement(getElement);
  let $$settled;
  let $$rendered;
  do {
    $$settled = true;
    $$rendered = `${validate_component(component || missing_component, "svelte:component").$$render($$result, Object_1.assign({ use: [forwardEvents, ...use] }, {
      class: classMap(__spreadValues({
        [className]: true,
        [smuiClass]: true
      }, smuiClassMap))
    }, props, $$restProps, { this: element }), {
      this: ($$value) => {
        element = $$value;
        $$settled = false;
      }
    }, {
      default: () => {
        return `${slots.default ? slots.default({}) : ``}`;
      }
    })}`;
  } while (!$$settled);
  return $$rendered;
});
const defaults = Object.assign({}, internals);
function classAdderBuilder(props) {
  return new Proxy(ClassAdder, {
    construct: function(target, args) {
      Object.assign(internals, defaults, props);
      return new target(...args);
    },
    get: function(target, prop) {
      Object.assign(internals, defaults, props);
      return target[prop];
    }
  });
}
export { A, Div as D, H5 as H, Li as L, Nav as N, Ripple as R, Span as S, Ul as U, classAdderBuilder as a, H6 as b, classMap as c, DefaultTabbar as d, H1 as e, forwardEventsBuilder as f, H2 as g, H3 as h, exclude as i, prefixFilter as p };
