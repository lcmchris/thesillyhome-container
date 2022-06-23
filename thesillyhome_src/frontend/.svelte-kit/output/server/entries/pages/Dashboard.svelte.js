import { c as create_ssr_component, v as validate_component, k as each, e as escape } from "../../chunks/index-f5246ab7.js";
import { d as DefaultTabbar } from "../../chunks/classAdderBuilder-56fb7b9f.js";
import { L as List, I as Item, G as Graphic, T as Text, P as PrimaryText, S as SecondaryText } from "../../chunks/index-76ee2332.js";
import "@material/tab-bar";
import "@material/tab-scroller";
import "@material/dom";
import "@material/tab";
import "@material/ripple";
import "@material/tab-indicator";
import "@material/list";
var Dashboard_svelte_svelte_type_style_lang = "";
const css = {
  code: ".dashboard-table.svelte-8wq8zw{position:relative;display:flex;height:350px;border:1px solid var(--mdc-theme-text-hint-on-background, rgba(0, 0, 0, 0.1));overflow:hidden;z-index:0;margin:100px 100px 100px 100px}.svelte-8wq8zw .act-list{max-width:600px}",
  map: null
};
const Dashboard = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { metrics } = $$props;
  let selection;
  if ($$props.metrics === void 0 && $$bindings.metrics && metrics !== void 0)
    $$bindings.metrics(metrics);
  $$result.css.add(css);
  return `${validate_component(DefaultTabbar, "DefaultTabbar").$$render($$result, { active: "Dashboard" }, {}, {})}

<div class="${"dashboard-table svelte-8wq8zw"}">${validate_component(List, "List").$$render($$result, {
    class: "act-list",
    twoLine: true,
    avatarList: true,
    singleSelection: true
  }, {}, {
    default: () => {
      return `${each(metrics, (metric) => {
        return `${validate_component(Item, "Item").$$render($$result, {
          disabled: metric.disabled,
          selected: selection === metric.actuator
        }, {}, {
          default: () => {
            return `${validate_component(Graphic, "Graphic").$$render($$result, {
              style: "background-image: url(/icons/light_icon.svg)"
            }, {}, {})}
				${validate_component(Text, "Text").$$render($$result, {}, {}, {
              default: () => {
                return `${validate_component(PrimaryText, "PrimaryText").$$render($$result, {}, {}, {
                  default: () => {
                    return `${escape(metric.actuator)}`;
                  }
                })}
					${validate_component(SecondaryText, "SecondaryText").$$render($$result, {}, {}, {
                  default: () => {
                    return `Accuracy = ${escape(metric.accuracy)}`;
                  }
                })}
				`;
              }
            })}
			`;
          }
        })}`;
      })}`;
    }
  })}
</div>`;
});
export { Dashboard as default };
