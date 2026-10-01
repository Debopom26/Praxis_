import java.io.File;
import java.io.Serializable;
import java.util.Map;
import java.util.HashMap;
import org.gradle.tooling.*;
import org.gradle.tooling.model.gradle.*;
import com.android.builder.model.v2.models.*;
import com.android.builder.model.v2.ide.*;

/** Reads actual AGP IDE models through Gradle Tooling API; does not launch Studio UI. */
public class CheckAndroidModel {
    public static class Inspect implements BuildAction<String>, Serializable {
        public String execute(BuildController controller) {
            GradleBuild build = controller.getBuildModel();
            BasicGradleProject app = build.getProjects().stream()
                .filter(p -> p.getPath().equals(":app")).findFirst().orElseThrow();
            BasicAndroidProject basic = controller.getModel(app, BasicAndroidProject.class);
            AndroidProject android = controller.getModel(app, AndroidProject.class);
            ProjectSyncIssues issues = controller.getModel(app, ProjectSyncIssues.class);
            if (!android.getNamespace().equals("com.praxis.caller")) throw new AssertionError("Namespace mismatch");
            if (basic.getProjectType() != ProjectType.APPLICATION) throw new AssertionError("Not an app");
            if (basic.getVariants().stream().noneMatch(v -> v.getName().equals("debug"))) throw new AssertionError("No debug variant");
            if (basic.getBootClasspath().isEmpty()) throw new AssertionError("No Android platform");
            StringBuilder result = new StringBuilder("Root: ").append(build.getRootProject().getName())
                .append("\nModule: ").append(basic.getPath()).append("\nNamespace: ").append(android.getNamespace())
                .append("\nType: ").append(basic.getProjectType()).append("\nVariants: ");
            basic.getVariants().forEach(v -> result.append(v.getName()).append(" "));
            result.append("\nBoot classpath: ").append(basic.getBootClasspath()).append("\nSync issues: ")
                .append(issues.getSyncIssues().size());
            for (SyncIssue issue : issues.getSyncIssues()) {
                result.append("\n").append(issue.getSeverity()).append(": ").append(issue.getMessage());
                if (issue.getSeverity() == SyncIssue.SEVERITY_ERROR) throw new AssertionError(result.toString());
            }
            return result.append("\nIDE-facing model validation: PASS\nAndroid Studio GUI launch: NOT RUN\n").toString();
        }
    }
    public static void main(String[] args) {
        File project = new File(args[0]), gradle = new File(args[1]), java = new File(args[2]), work = new File(args[3]);
        Map<String,String> env = new HashMap<>(System.getenv());
        env.put("JAVA_HOME", java.getAbsolutePath());
        env.put("GRADLE_USER_HOME", new File(work,"gradle-home").getAbsolutePath());
        env.put("ANDROID_USER_HOME", new File(work,"android-user").getAbsolutePath());
        env.put("ANDROID_HOME", new File(args[4]).getAbsolutePath());
        try (ProjectConnection connection = GradleConnector.newConnector().forProjectDirectory(project)
                .useInstallation(gradle).useGradleUserHomeDir(new File(work,"gradle-home")).connect()) {
            System.out.println(connection.action(new Inspect()).setJavaHome(java).setEnvironmentVariables(env)
                .setStandardOutput(System.out).setStandardError(System.err).run());
        }
    }
}
