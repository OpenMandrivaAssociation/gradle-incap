Name:		gradle-incap
Version:	1.0.0
Release:	1
Summary:	Incremental annotation processor marker
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/tbroyer/gradle-incap-helper
Source0:	https://github.com/tbroyer/gradle-incap-helper/archive/refs/tags/v%{version}.tar.gz#/gradle-incap-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar

%description
gradle-incap %{version} marks an annotation processor as isolating,
aggregating, or dynamic. AutoValue declares this marker so Gradle can
run the processor incrementally.

%prep
%autosetup -n gradle-incap-helper-%{version} -p1
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete

%build
find lib/src/main/java -name '*.java' ! -name 'module-info.java' > sources.list
test "$(wc -l < sources.list)" -eq 2
mkdir -p classes
javac --release 8 -encoding UTF-8 -d classes @sources.list
jar cf incap.jar -C classes .
jar tf incap.jar | grep -E '\.(java|jar|so|node|wasm)$' && exit 1 || true
javap -verbose -cp incap.jar net.ltgt.gradle.incap.IncrementalAnnotationProcessorType | grep -F 'major version: 52'

cat > incap.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>net.ltgt.gradle.incap</groupId>
  <artifactId>incap</artifactId>
  <version>1.0.0</version>
  <name>Incremental annotation processor marker</name>
  <description>Incremental annotation processor marker</description>
  <licenses>
    <license>
      <name>Apache-2.0</name>
    </license>
  </licenses>
</project>
EOF

%install
sysjar install --buildroot %{buildroot} \
	--artifact incap.pom:incap.jar \
	--file-name incap \
	--filelist .mfiles

%check
mkdir -p check
cat > check/Smoke.java << 'END'
import net.ltgt.gradle.incap.IncrementalAnnotationProcessor;
import net.ltgt.gradle.incap.IncrementalAnnotationProcessorType;
public class Smoke {
	public static void main(String[] args) {
		IncrementalAnnotationProcessorType type = IncrementalAnnotationProcessorType.ISOLATING;
		System.out.println("incap_ok " + type.getProcessorOption()
			+ " " + IncrementalAnnotationProcessor.class.getSimpleName());
	}
}
END
JAR=%{buildroot}%{_javadir}/incap.jar
test -f "$JAR"
javac --release 8 -encoding UTF-8 -cp "$JAR" -d check check/Smoke.java
java -cp "check:$JAR" Smoke > check/out.txt
cat check/out.txt
grep -F -q 'incap_ok org.gradle.annotation.processing.isolating IncrementalAnnotationProcessor' check/out.txt

%files -f .mfiles
%doc LICENSE README.md
