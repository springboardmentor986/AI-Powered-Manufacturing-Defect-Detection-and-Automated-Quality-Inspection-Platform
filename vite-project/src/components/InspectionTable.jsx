function InspectionTable() {
  const inspections = [
    {
      id: "INS001",
      product: "Bottle",
      date: "23 Aug 2026",
      result: "PASS",
      confidence: "98.2%",
    },
    {
      id: "INS002",
      product: "Cable",
      date: "23 Aug 2026",
      result: "DEFECT",
      confidence: "91.7%",
    },
    {
      id: "INS003",
      product: "Screw",
      date: "22 Aug 2026",
      result: "PASS",
      confidence: "96.4%",
    },
    {
      id: "INS004",
      product: "Metal Part",
      date: "22 Aug 2026",
      result: "DEFECT",
      confidence: "89.3%",
    },
    {
      id: "INS005",
      product: "Bottle",
      date: "21 Aug 2026",
      result: "PASS",
      confidence: "97.1%",
    },
  ];

  return (
    <div className="w-full">

      {/* HEADER */}
      <div className="flex items-center justify-between mb-5">

        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            Recent Inspections
          </h2>

          <p className="text-sm text-slate-500 mt-1">
            Latest quality inspection results
          </p>
        </div>

        <button
          type="button"
          className="text-sm font-medium text-blue-600 hover:text-blue-700"
        >
          View All
        </button>

      </div>

      {/* TABLE */}
      <div className="overflow-x-auto rounded-lg border border-slate-200">

        <table className="w-full text-sm">

          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>

              <th className="px-5 py-3 text-left font-semibold text-slate-600">
                Inspection ID
              </th>

              <th className="px-5 py-3 text-left font-semibold text-slate-600">
                Product
              </th>

              <th className="px-5 py-3 text-left font-semibold text-slate-600">
                Date
              </th>

              <th className="px-5 py-3 text-left font-semibold text-slate-600">
                Result
              </th>

              <th className="px-5 py-3 text-left font-semibold text-slate-600">
                Confidence
              </th>

              <th className="px-5 py-3 text-left font-semibold text-slate-600">
                Action
              </th>

            </tr>
          </thead>

          <tbody className="divide-y divide-slate-100">

            {inspections.map((inspection) => (

              <tr
                key={inspection.id}
                className="hover:bg-slate-50 transition"
              >

                <td className="px-5 py-4 font-semibold text-slate-800">
                  {inspection.id}
                </td>

                <td className="px-5 py-4 text-slate-600">
                  {inspection.product}
                </td>

                <td className="px-5 py-4 text-slate-500">
                  {inspection.date}
                </td>

                <td className="px-5 py-4">

                  <span
                    className={
                      inspection.result === "PASS"
                        ? "inline-flex items-center rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-green-700"
                        : "inline-flex items-center rounded-full bg-red-50 px-3 py-1 text-xs font-semibold text-red-700"
                    }
                  >
                    {inspection.result}
                  </span>

                </td>

                <td className="px-5 py-4 font-medium text-slate-700">
                  {inspection.confidence}
                </td>

                <td className="px-5 py-4">

                  <button
                    type="button"
                    className="text-sm font-medium text-blue-600 hover:text-blue-800"
                  >
                    View
                  </button>

                </td>

              </tr>

            ))}

          </tbody>

        </table>

      </div>

    </div>
  );
}

export default InspectionTable;